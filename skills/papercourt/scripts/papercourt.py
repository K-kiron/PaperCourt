#!/usr/bin/env python3
"""Local evidence reports for empirical ML claims. Python 3.10+, standard library."""

import argparse
import csv
import hashlib
import html
import io
import json
import re
import sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from urllib.parse import quote as urlquote

VERSION = "0.1.0"
STATUSES = {"supported_within_scope", "limited", "conflicting_evidence", "unknown"}
BASE_CONDITIONS = ("dataset", "split", "metric", "unit", "protocol")
MAX_BYTES = 5_000_000
RESERVED_IDS = {"con", "prn", "aux", "nul"} | {f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10)}


class InputError(ValueError):
    """The review specification or a supplied artifact is invalid."""


def need(ok, message):
    if not ok:
        raise InputError(message)


def fields(value, required, optional=()):
    need(isinstance(value, dict), "Expected a JSON object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    need(not missing and not extra, f"Invalid fields: missing={sorted(missing)}, extra={sorted(extra)}")


def string(value, label):
    need(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    return value


def sequence(value, label, minimum=0):
    need(isinstance(value, list) and len(value) >= minimum, f"{label} must be an array (minimum {minimum})")
    return value


def number(value):
    need(type(value) in (str, int, float), f"Expected numeric scalar, got {value!r}")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise InputError(f"Invalid number: {value!r}") from exc
    need(result.is_finite(), f"Non-finite number: {value!r}")
    need(abs(result.adjusted()) <= 100 if result else True, "Numeric exponent is too large")
    return result


def fmt(value):
    return format(value, "f")


def strict_json(text):
    def pairs(items):
        obj = {}
        for key, value in items:
            need(key not in obj, f"Duplicate JSON key: {key}")
            obj[key] = value
        return obj

    def invalid(value):
        raise InputError(f"Non-finite JSON constant: {value}")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid, parse_float=str)
    except (json.JSONDecodeError, ValueError) as exc:
        raise InputError(f"Invalid JSON: {exc}") from exc


def read_bytes(path):
    need(path.is_file(), f"File not found: {path.name}")
    need(path.stat().st_size <= MAX_BYTES, f"File exceeds {MAX_BYTES} bytes: {path.name}")
    return path.read_bytes()


def decode(raw):
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("Inputs must be UTF-8 text") from exc


def source(path, label):
    raw = read_bytes(path)
    text = decode(raw)
    result = {"path": label, "sha256": hashlib.sha256(raw).hexdigest(), "_raw": raw,
              "text": text, "lines": text.splitlines(), "rows": None}
    if path.suffix.lower() == ".csv":
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)
        need(header and all(header) and len(header) == len(set(header)), "CSV headers must be nonempty and unique")
        rows = []
        previous = reader.line_num
        for values in reader:
            start = previous + 1
            previous = reader.line_num
            need(len(values) == len(header), f"CSV width mismatch at line {start}")
            rows.append({"data": dict(zip(header, values)), "start": start, "end": previous})
        result["rows"] = rows
    elif path.suffix.lower() == ".json":
        records = strict_json(text)
        sequence(records, "JSON results")
        rows = []
        for i, record in enumerate(records):
            need(isinstance(record, dict), "JSON results must be an array of objects")
            need(all(v is None or type(v) in (str, int, float, bool) for v in record.values()),
                 "JSON result fields must be scalar values")
            rows.append({"data": record, "start": 1, "end": len(result["lines"]), "pointer": f"/{i}"})
        result["rows"] = rows
    return result


def load_case(path):
    path = Path(path).resolve()
    raw = read_bytes(path)
    case = strict_json(decode(raw))
    fields(case, ("version", "title", "sources", "claims"))
    need(type(case["version"]) is int and case["version"] == 1, "Unsupported case version")
    string(case["title"], "title")
    need(isinstance(case["sources"], dict) and case["sources"], "sources must be a nonempty object")
    sources = {}
    source_ids = set()
    for key, relative in case["sources"].items():
        need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key), "Source IDs must be simple ASCII identifiers")
        need(key.lower() not in source_ids and key.lower() not in RESERVED_IDS,
             "Source IDs must be unique ignoring case and cannot be Windows device names")
        source_ids.add(key.lower())
        string(relative, "source path")
        relative_path = Path(relative)
        need(not relative_path.is_absolute() and ".." not in relative_path.parts,
             "Source paths must stay inside the case directory")
        resolved = (path.parent / relative_path).resolve()
        need(resolved.is_relative_to(path.parent), "Source path escapes the case directory")
        need(resolved != path, "The case cannot be its own evidence")
        need(resolved.suffix.lower() in (".md", ".tex", ".txt", ".csv", ".json"), "Unsupported source extension")
        sources[key] = source(resolved, relative_path.as_posix())
    sequence(case["claims"], "claims", 1)
    return case, sources, raw


def locate(ref, sources, row_only=False):
    need(isinstance(ref, dict), "Evidence reference must be an object")
    is_row = "row" in ref
    if is_row:
        fields(ref, ("source", "row"), ("field",))
    else:
        fields(ref, ("source", "start", "end", "quote"))
    need(not row_only or is_row, "Numeric operands must select result rows")
    key = string(ref["source"], "source")
    need(key in sources, f"Undeclared source: {key}")
    src = sources[key]
    if not is_row:
        start, end = ref["start"], ref["end"]
        need(type(start) is int and type(end) is int and 1 <= start <= end <= len(src["lines"]), "Invalid evidence line span")
        excerpt = "\n".join(src["lines"][start - 1:end])
        quote = string(ref["quote"], "quote")
        need(quote in excerpt, f"Quote does not match {key}:{start}-{end}")
        return {"source": key, "start": start, "end": end, "excerpt": excerpt, "quote": quote}
    need(src["rows"] is not None, "Row reference requires CSV or JSON results")
    selector = ref["row"]
    need(isinstance(selector, dict) and selector, "Row selector must be a nonempty object")
    for val in selector.values():
        need(type(val) in (str, int, float), "Selectors must contain string or numeric values")
    matches = [row for row in src["rows"] if all(k in row["data"] and str(row["data"][k]) == str(v) for k, v in selector.items())]
    need(len(matches) <= 1, f"Ambiguous row selector in {key}: {selector}")
    result = {"source": key, "selector": selector}
    if not matches:
        return {**result, "missing": "No matching row in the supplied source"}
    row = matches[0]
    result.update({k: v for k, v in row.items() if k != "data"})
    result["record"] = row["data"]
    result["excerpt"] = "\n".join(src["lines"][row["start"] - 1:row["end"]])
    if "field" in ref:
        field = string(ref["field"], "field")
        result["field"] = field
        if field not in row["data"] or row["data"][field] in (None, ""):
            result["missing"] = f"Missing value in field {field}"
        else:
            result["value"] = row["data"][field]
    return result


def conditions(operands, keys):
    if len(operands) == 1:
        return {"status": "not_applicable", "fields": {}}
    details = {}
    for key in keys:
        values = [ref.get("record", {}).get(key) for ref in operands]
        missing = any(v is None or v == "" for v in values)
        state = "unknown" if missing else ("aligned" if all(str(v) == str(values[0]) for v in values) else "different")
        details[key] = {"status": state, "values": values}
    states = [v["status"] for v in details.values()]
    status = "different" if "different" in states else ("unknown" if "unknown" in states else "aligned")
    return {"status": status, "fields": details}


def check_numeric(check, sources):
    fields(check, ("operation", "operands", "expected", "tolerance", "unit", "conditions"))
    op = string(check["operation"], "operation")
    need(op in ("value", "difference", "relative_change", "ratio", "mean"), "Unknown numeric operation")
    refs = sequence(check["operands"], "operands", 1)
    need((op == "mean") or len(refs) == (1 if op == "value" else 2), f"Wrong operand count for {op}")
    expected, tolerance = number(check["expected"]), number(check["tolerance"])
    need(tolerance >= 0, "Tolerance must be nonnegative")
    string(check["unit"], "unit")
    keys = sequence(check["conditions"], "conditions")
    need(all(isinstance(k, str) and k for k in keys) and len(keys) == len(set(keys)), "conditions must be unique field names")
    if len(refs) > 1:
        need(set(BASE_CONDITIONS) <= set(keys), f"Comparison conditions must include {', '.join(BASE_CONDITIONS)}")
    operands = [locate(ref, sources, row_only=True) for ref in refs]
    need(all("field" in ref for ref in refs), "Each numeric operand requires a field")
    result = {"operation": op, "expected": fmt(expected), "tolerance": fmt(tolerance),
              "unit": check["unit"], "operands": operands, "conditions": conditions(operands, keys)}
    if any("missing" in ref for ref in operands):
        return {**result, "status": "unknown", "reason": "An operand is missing; no numeric conclusion"}
    values = [number(ref["value"]) for ref in operands]
    if op in ("ratio", "relative_change") and values[1] <= 0:
        return {**result, "status": "unknown", "reason": "Ratio/relative-change baseline must be positive"}
    with localcontext() as context:
        context.prec = 50
        if op == "value":
            actual = values[0]
        elif op == "difference":
            actual = values[0] - values[1]
        elif op == "relative_change":
            actual = (values[0] - values[1]) / values[1] * 100
        elif op == "ratio":
            actual = values[0] / values[1]
        else:
            actual = sum(values) / len(values)
        delta = abs(actual - expected)
    return {**result, "status": "consistent" if delta <= tolerance else "inconsistent",
            "actual": fmt(actual), "absolute_error": fmt(delta)}


def audit(case_path):
    case, sources, case_raw = load_case(case_path)
    claims, ids = [], set()
    for claim in case["claims"]:
        fields(claim, ("id", "statement", "numeric", "assessment"))
        cid = string(claim["id"], "claim id")
        need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", cid) and cid.lower() not in ids, "Claim IDs must be unique ASCII identifiers ignoring case")
        ids.add(cid.lower())
        need(isinstance(claim["statement"], dict) and "row" not in claim["statement"], "A statement requires a text quote and line span")
        statement = locate(claim["statement"], sources)
        numeric = [check_numeric(check, sources) for check in sequence(claim["numeric"], "numeric")]
        a = claim["assessment"]
        fields(a, ("status", "reason", "evidence", "limitations", "next_check", "falsifier"))
        need(string(a["status"], "status") in STATUSES, "Invalid model-analysis status")
        for field in ("reason", "limitations", "next_check", "falsifier"):
            string(a[field], field)
        evidence = [locate(ref, sources) for ref in sequence(a["evidence"], "evidence")]
        if a["status"] != "unknown":
            need(evidence and any("missing" not in ref for ref in evidence), "Non-unknown model analysis needs located evidence")
        claims.append({"id": cid, "statement": statement, "numeric": numeric,
                       "assessment": {**a, "origin": "model_analysis", "evidence": evidence}})
    return {"version": VERSION, "title": case["title"], "case_sha256": hashlib.sha256(case_raw).hexdigest(),
            "_case_raw": case_raw, "case_file": Path(case_path).name,
            "claims": claims, "sources": sources}


def plain(value):
    return html.escape(str(value), quote=True)


def markdown(value):
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(str(value), quote=False)).replace("\n", " ")


def reference_label(ref):
    location = f"{ref['source']}:{ref.get('start', 1)}"
    if "pointer" in ref:
        location += f" (JSON {ref['pointer']})"
    if "field" in ref:
        location += f" [{ref['field']}]"
    if "selector" in ref:
        location += " " + json.dumps(ref["selector"], ensure_ascii=False, sort_keys=True)
    if "missing" in ref:
        location += " — " + ref["missing"]
    return location


def evidence_link(ref, web=False):
    key, line = ref["source"], ref.get("start", 1)
    label = reference_label(ref)
    if web:
        return f'<a href="#src-{key}-L{line}">{plain(label)}</a>'
    return f"[{markdown(label)}](evidence/{key}.md#line-{line})"


def numeric_summary(check):
    if "actual" not in check:
        return f"{check['operation']}: {check['status']} — {check['reason']}"
    return (f"{check['operation']}: {check['status']} — computed {check['actual']}; "
            f"claimed {check['expected']} ± {check['tolerance']} {check['unit']}. "
            f"Selected conditions: {check['conditions']['status']}.")


def render_markdown(report):
    lines = [f"# {markdown(report['title'])}", "", "PaperCourt evidence report", "",
             "Arithmetic and selected metadata are script-checked. Support assessments are model analysis, not academic verdicts. Missing evidence means unknown. Proposed checks have not been run.", "",
             f"Case SHA-256: `{report['case_sha256']}`", "",
             "| Claim | Model assessment | Numeric checks | Selected conditions |",
             "| --- | --- | --- | --- |"]
    for c in report["claims"]:
        nums = ", ".join(n["status"] for n in c["numeric"]) or "not checked"
        cond = ", ".join(n["conditions"]["status"] for n in c["numeric"]) or "not checked"
        lines.append(f"| [{c['id']}](#{c['id'].lower()}) | {c['assessment']['status']} | {nums} | {cond} |")
    for c in report["claims"]:
        a = c["assessment"]
        lines += ["", f"## {c['id']}", "", markdown(c["statement"]["quote"]), "", evidence_link(c["statement"]), "",
                  f"**Model analysis: {a['status']}**", "", markdown(a["reason"]), "", "Evidence:", ""]
        lines += ["- " + evidence_link(ref) for ref in a["evidence"]] or ["No evidence mapped; status remains unknown."]
        for n in c["numeric"]:
            lines += ["", "**Script check**", "", markdown(numeric_summary(n)), ""]
            lines += ["- " + evidence_link(ref) for ref in n["operands"]]
            for key, detail in n["conditions"]["fields"].items():
                lines += ["- " + markdown(f"{key}: {detail['status']} — {json.dumps(detail['values'], ensure_ascii=False)}")]
        for label, key in (("Limitations", "limitations"), ("Minimum next check (proposed)", "next_check"), ("Observable falsifier", "falsifier")):
            lines += ["", f"**{label}:** {markdown(a[key])}"]
    lines += ["", "## Source inventory", "", "Snapshots preserve the reviewed evidence. Hashes identify exact input bytes; they do not prove authenticity.", ""]
    for key, src in report["sources"].items():
        lines += [f"- [{key}](evidence/{key}.md): {markdown(src['path'])} — SHA-256 `{src['sha256']}`"]
    return "\n".join(lines) + "\n"


STYLE = """
:root{color-scheme:light;--ink:#17252a;--muted:#496069;--line:#c9d8d6;--accent:#12675e}
*{box-sizing:border-box}body{margin:0;background:#f4f6f2;color:var(--ink);font:16px/1.6 system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:48px 28px}header{border-top:6px solid var(--accent);padding:24px 0}
h1{font-size:clamp(30px,5vw,52px);line-height:1.12;max-width:880px;margin:14px 0}h2{margin-top:0}
a{color:var(--accent);overflow-wrap:anywhere}a:focus-visible{outline:3px solid #ab552a;outline-offset:3px}
.eyebrow{letter-spacing:.16em;font-weight:700;font-size:12px}.subtle{color:var(--muted)}
.claims{display:grid;gap:22px}.claim{background:white;border:1px solid var(--line);border-radius:10px;padding:26px}
.badge{display:inline-block;background:#e4efea;border-radius:4px;padding:3px 10px;font-size:13px;font-weight:650}
.badge.limited,.badge.inconsistent,.badge.different,.badge.conflicting_evidence{background:#ffe9d9;color:#773a17}
.badge.unknown{background:#ececf3;color:#47475c}blockquote{border-left:3px solid var(--accent);margin:18px 0;padding-left:18px;font-size:19px}
.check{background:#f4f6f2;padding:18px;border-radius:5px;margin:18px 0}ul{padding-left:22px}
dl{display:grid;grid-template-columns:190px 1fr;gap:10px 22px}dt{font-weight:650}dd{margin:0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.7 ui-monospace,monospace;background:#edf1ed;padding:12px;border-radius:4px}
.line{display:block;scroll-margin-top:20px}.line:target{background:#ffe1a0;outline:2px solid #ae671d}
.ln{display:inline-block;min-width:4em;color:#526565;user-select:none}.source{margin-top:38px}.hash{overflow-wrap:anywhere;font:12px/1.5 ui-monospace,monospace}
nav{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}nav a{border:1px solid var(--line);padding:6px 14px;border-radius:4px;text-decoration:none}
@media(max-width:650px){main{padding:24px 16px}.claim{padding:18px}dl{grid-template-columns:1fr;gap:4px}dd{margin-bottom:12px}}
@media print{body{background:white}.claim{break-inside:avoid}nav{display:none}}
"""


def render_html(report):
    chunks = ["<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">",
              '<meta name="viewport" content="width=device-width,initial-scale=1">',
              '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'">',
              f"<title>{plain(report['title'])} | PaperCourt</title><style>{STYLE}</style><main>",
              '<header><div class="eyebrow">PAPERCOURT / EVIDENCE REPORT</div>',
              f"<h1>{plain(report['title'])}</h1>",
              '<p class="subtle">Repeatable arithmetic. Inspectable sources. Testable next steps.</p>',
              '<p>Script checks cover arithmetic and selected metadata. Support assessments are <strong>model analysis</strong>, not academic verdicts. Missing evidence means unknown. Proposed checks have not been run.</p>',
              f'<p class="hash">Case SHA-256: {report["case_sha256"]}</p></header><nav aria-label="Claims">']
    chunks += [f'<a href="#claim-{c["id"]}">{c["id"]}</a>' for c in report["claims"]]
    chunks += ['<a href="#sources">Sources</a></nav><section class="claims" aria-label="Claim reports">']
    for c in report["claims"]:
        a = c["assessment"]
        chunks += [f'<article class="claim" id="claim-{c["id"]}"><h2>{c["id"]}</h2>',
                   f'<span class="badge {a["status"]}">Model analysis · {a["status"]}</span>',
                   f'<blockquote>{plain(c["statement"]["quote"])}</blockquote><p>{evidence_link(c["statement"], True)}</p>',
                   f'<p>{plain(a["reason"])}</p><ul>']
        chunks += [f"<li>{evidence_link(ref, True)}</li>" for ref in a["evidence"]]
        chunks += ["</ul>"]
        for n in c["numeric"]:
            chunks += [f'<section class="check"><span class="badge {n["status"]}">Script check · {n["status"]}</span>',
                       f'<p>{plain(numeric_summary(n))}</p><ul>']
            chunks += [f"<li>{evidence_link(ref, True)}</li>" for ref in n["operands"]]
            chunks += ["</ul><ul>"]
            chunks += [f"<li>{plain(key)}: <strong>{detail['status']}</strong> — {plain(json.dumps(detail['values'], ensure_ascii=False))}</li>" for key, detail in n["conditions"]["fields"].items()]
            chunks += ["</ul></section>"]
        chunks += ["<dl>"]
        for label, key in (("Limitations", "limitations"), ("Minimum next check", "next_check"), ("Observable falsifier", "falsifier")):
            chunks += [f"<dt>{label}</dt><dd>{plain(a[key])}</dd>"]
        chunks += ["</dl></article>"]
    chunks += ['</section><section id="sources"><h2>Source snapshots</h2><p>Hashes identify exact input bytes; they do not establish authenticity. These snapshots contain the supplied material.</p>']
    for key, src in report["sources"].items():
        chunks += [f'<article class="source"><h3>{plain(key)} · {plain(src["path"])}</h3><p class="hash">SHA-256: {src["sha256"]}</p><pre>']
        for i, line in enumerate(src["lines"], 1):
            chunks += [f'<span class="line" id="src-{key}-L{i}"><a class="ln" href="#src-{key}-L{i}" aria-label="Line {i}">{i}</a>{plain(line)}</span>']
        chunks += ["</pre></article>"]
    chunks += [f"</section><footer><p>PaperCourt {VERSION} · Local report · No external assets</p></footer></main></html>"]
    return "\n".join(chunks) + "\n"


def write_report(report, output):
    output = Path(output)
    need(not output.exists(), "Output directory already exists; choose a new directory")
    # Render before creating the output directory so malformed data leaves no partial report.
    md, page = render_markdown(report), render_html(report)
    public = {k: v for k, v in report.items() if not k.startswith("_")}
    public["sources"] = {key: {k: v for k, v in src.items() if not k.startswith("_")}
                         for key, src in report["sources"].items()}
    json_text = json.dumps(public, indent=2, ensure_ascii=False) + "\n"
    output.mkdir(parents=True)
    (output / "evidence").mkdir()
    (output / "inputs").mkdir()
    (output / "inputs" / report["case_file"]).write_bytes(report["_case_raw"])
    (output / "report.md").write_text(md, encoding="utf-8", newline="\n")
    (output / "report.html").write_text(page, encoding="utf-8", newline="\n")
    (output / "report.json").write_text(json_text, encoding="utf-8", newline="\n")
    for key, src in report["sources"].items():
        original = output / "inputs" / src["path"]
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(src["_raw"])
        lines = [f"# {markdown(src['path'])}", "", f"SHA-256: `{src['sha256']}`", "",
                 f"[Original bytes](../inputs/{urlquote(src['path'])})", ""]
        for i, line in enumerate(src["lines"], 1):
            lines += [f"## Line {i}", "", "    " + line if line else "", ""]
        (output / "evidence" / f"{key}.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("audit", help="Verify a case and generate Markdown, HTML, and JSON reports")
    cmd.add_argument("case", type=Path)
    cmd.add_argument("--out", required=True, type=Path, help="New output directory; never overwrites")
    cmd.add_argument("--fail-on-inconsistency", action="store_true", help="Return 1 for a numeric discrepancy or differing selected conditions")
    args = parser.parse_args(argv)
    try:
        report = audit(args.case)
        write_report(report, args.out)
        checks = [n for c in report["claims"] for n in c["numeric"]]
        discrepancies = sum(n["status"] == "inconsistent" for n in checks)
        different = sum(n["conditions"]["status"] == "different" for n in checks)
        unknown = sum(n["status"] == "unknown" or n["conditions"]["status"] == "unknown" for n in checks)
        print(f"Reviewed {len(report['claims'])} claims; {len(checks)} numeric checks; {discrepancies} numeric discrepancies; {different} differing comparisons; {unknown} checks with unknowns.")
        print(f"Report: {args.out / 'report.html'}")
        return 1 if args.fail_on_inconsistency and (discrepancies or different) else 0
    except (InputError, OSError, csv.Error) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
