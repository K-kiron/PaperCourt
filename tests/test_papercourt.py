"""Behavior tests use real files, selectors, CLI exits, and generated evidence links."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/papercourt/scripts/papercourt.py"
spec = importlib.util.spec_from_file_location("papercourt", SCRIPT)
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)
install_spec = importlib.util.spec_from_file_location("install_skill", ROOT / "tools/install_skill.py")
installer = importlib.util.module_from_spec(install_spec)
install_spec.loader.exec_module(installer)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.tags = set(), [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if "href" in attrs:
            self.hrefs.append(attrs["href"])


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="PaperCourt-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("paper.md", "results.csv", "runtime.json", "case.json"):
            (self.root / name).write_bytes((ROOT / "examples/tiny-ml" / name).read_bytes())
        self.case = json.loads((self.root / "case.json").read_text())

    def run_case(self):
        (self.root / "case.json").write_text(json.dumps(self.case), encoding="utf-8")
        return pc.audit(self.root / "case.json")

    def check(self, claim=2):
        return self.case["claims"][claim]["numeric"][0]

    def test_worked_example_preserves_independent_verdict_layers(self):
        report = self.run_case()
        claims = report["claims"]
        self.assertEqual(claims[1]["numeric"][0]["status"], "consistent")
        self.assertEqual(claims[2]["numeric"][0]["actual"], "2.0")
        self.assertEqual(claims[2]["numeric"][0]["status"], "inconsistent")
        self.assertEqual(claims[3]["numeric"][0]["status"], "consistent")
        self.assertEqual(claims[3]["numeric"][0]["conditions"]["status"], "different")
        self.assertEqual(claims[4]["assessment"]["status"], "unknown")
        self.assertEqual(claims[5]["numeric"][0]["actual"], "2.500")
        self.assertTrue(all(c["assessment"]["origin"] == "model_analysis" for c in claims))

    def test_missing_result_is_unknown_not_false(self):
        self.check()["operands"][0]["row"] = {"id": "absent"}
        result = self.run_case()["claims"][2]["numeric"][0]
        self.assertEqual(result["status"], "unknown")
        self.assertNotIn("actual", result)

    def test_missing_condition_cannot_be_called_aligned(self):
        self.check()["conditions"].append("tuning_budget")
        result = self.run_case()["claims"][2]["numeric"][0]
        self.assertEqual(result["conditions"]["status"], "unknown")

    def test_different_condition_stays_visible_amid_missing_controls(self):
        self.check(3)["conditions"].append("warmup")
        result = self.run_case()["claims"][3]["numeric"][0]
        self.assertEqual(result["conditions"]["status"], "different")
        self.assertEqual(result["conditions"]["fields"]["warmup"]["status"], "unknown")

    def test_missing_value_is_unknown(self):
        self.check()["operands"][0]["field"] = "unreported_accuracy"
        self.assertEqual(self.run_case()["claims"][2]["numeric"][0]["status"], "unknown")

    def test_ambiguous_rows_are_rejected(self):
        path = self.root / "results.csv"
        path.write_text(path.read_text() + path.read_text().splitlines()[1] + "\n")
        with self.assertRaisesRegex(pc.InputError, "Ambiguous"):
            self.run_case()

    def test_stale_quote_is_rejected(self):
        self.case["claims"][0]["statement"]["quote"] = "This was never in the paper"
        with self.assertRaisesRegex(pc.InputError, "Quote does not match"):
            self.run_case()

    def test_empty_evidence_cannot_support_model_conclusion(self):
        self.case["claims"][0]["assessment"]["evidence"] = []
        with self.assertRaisesRegex(pc.InputError, "needs located evidence"):
            self.run_case()

    def test_decimal_boundary_tolerance(self):
        self.check()["expected"] = "2.05"
        self.assertEqual(self.run_case()["claims"][2]["numeric"][0]["status"], "consistent")
        self.check()["expected"] = "2.0500001"
        self.assertEqual(self.run_case()["claims"][2]["numeric"][0]["status"], "inconsistent")

    def test_relative_change_rejects_nonpositive_baseline(self):
        for value in ("0", "-1"):
            with self.subTest(value=value):
                path = self.root / "results.csv"
                original = (ROOT / "examples/tiny-ml/results.csv").read_text()
                path.write_text(original.replace("80.0", value))
                result = self.run_case()["claims"][5]["numeric"][0]
                self.assertEqual(result["status"], "unknown")

    def test_nonfinite_values_and_boolean_are_rejected(self):
        for value in ("NaN", "Infinity", True, "1e999999"):
            with self.subTest(value=value), self.assertRaises(pc.InputError):
                pc.number(value)

    def test_comparison_cannot_omit_basic_conditions(self):
        self.check()["conditions"] = ["dataset"]
        with self.assertRaisesRegex(pc.InputError, "must include"):
            self.run_case()

    def test_mean_is_unweighted_and_decimal(self):
        self.check()["operation"] = "mean"
        self.check()["expected"] = "81.0"
        result = self.run_case()["claims"][2]["numeric"][0]
        self.assertEqual(result["status"], "consistent")
        self.assertEqual(result["actual"], "81.0")

    def test_path_escape_is_rejected(self):
        for path in ("../secret.md", str(self.root.parent / "secret.md")):
            with self.subTest(path=path):
                self.case["sources"]["paper"] = path
                with self.assertRaisesRegex(pc.InputError, "inside the case"):
                    self.run_case()

    def test_source_ids_cannot_collide_on_windows(self):
        for key in ("Paper", "CON", "aux"):
            with self.subTest(key=key):
                self.case["sources"][key] = "paper.md"
                with self.assertRaisesRegex(pc.InputError, "unique ignoring case"):
                    self.run_case()
                del self.case["sources"][key]

    def test_claim_ids_cannot_make_duplicate_markdown_anchors(self):
        self.case["claims"][1]["id"] = "c1"
        with self.assertRaisesRegex(pc.InputError, "unique ASCII"):
            self.run_case()

    def test_unknown_or_misspelled_fields_are_rejected(self):
        self.check()["tolerence"] = "0.05"
        with self.assertRaisesRegex(pc.InputError, "extra"):
            self.run_case()

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(pc.InputError, "Duplicate"):
            pc.strict_json('{"x": 1, "x": 2}')

    def test_json_decimals_keep_the_supplied_precision(self):
        path = self.root / "decimal.json"
        path.write_text('[{"id":"a", "value":0.10000000000000001}]')
        src = pc.source(path, "decimal.json")
        check = dict(operation="value", operands=[dict(source="r", row={"id":"a"}, field="value")],
                     expected="0.1", tolerance="0", unit="fraction", conditions=[])
        result = pc.check_numeric(check, {"r":src})
        self.assertEqual(result["status"], "inconsistent")
        self.assertEqual(result["actual"], "0.10000000000000001")

    def test_wrong_json_types_are_input_errors(self):
        for field, value in (("operation", []), ("unit", None), ("conditions", {})):
            with self.subTest(field=field):
                original = self.check()[field]
                self.check()[field] = value
                with self.assertRaises(pc.InputError):
                    self.run_case()
                self.check()[field] = original

    def test_multiline_csv_preserves_physical_lines(self):
        path = self.root / "multiline.csv"
        path.write_text('id,note,value\na,"two\nlines",0.3\nb,plain,0.2\n', encoding="utf-8")
        src = pc.source(path, "multiline.csv")
        ref = pc.locate({"source": "r", "row": {"id": "a"}, "field": "value"}, {"r": src})
        self.assertEqual((ref["start"], ref["end"]), (2, 3))
        self.assertEqual(ref["value"], "0.3")

    def test_duplicate_csv_headers_and_ragged_rows_are_rejected(self):
        path = self.root / "bad.csv"
        for text in ("id,id\na,b\n", "id,value\na,1,extra\n"):
            with self.subTest(text=text):
                path.write_text(text)
                with self.assertRaises(pc.InputError):
                    pc.source(path, "bad.csv")

    def test_bom_utf8_and_latex_are_read_without_execution(self):
        path = self.root / "paper.tex"
        path.write_bytes(b'\xef\xbb\xbf' + 'A $\\delta$ claim.\n\\input{unread.tex}\n'.encode())
        src = pc.source(path, "paper.tex")
        ref = pc.locate(dict(source="p", start=1, end=1, quote="claim"), {"p": src})
        self.assertEqual(ref["start"], 1)

    def test_report_links_resolve_and_source_html_is_inert(self):
        report = self.run_case()
        report["title"] = '<script>alert("x")</script>'
        report["sources"]["paper"]["lines"][0] = '<img src="https://invalid.example/tracker">'
        page = pc.render_html(report)
        parser = Links()
        parser.feed(page)
        self.assertTrue(all(h[1:] in parser.ids for h in parser.hrefs if h.startswith("#")))
        self.assertNotIn("script", parser.tags)
        self.assertNotIn("img", parser.tags)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Content-Security-Policy", page)

    def test_markdown_evidence_links_and_snapshot_hashes(self):
        report = self.run_case()
        out = self.root / "review"
        pc.write_report(report, out)
        self.assertIn("evidence/results.md#line-2", (out / "report.md").read_text(encoding="utf-8"))
        self.assertIn("## Line 2", (out / "evidence/results.md").read_text(encoding="utf-8"))
        before = report["sources"]["results"]["sha256"]
        self.assertEqual((out / "inputs/results.csv").read_bytes(), (self.root / "results.csv").read_bytes())
        replay = pc.audit(out / "inputs/case.json")
        self.assertEqual(replay["claims"], report["claims"])
        self.assertEqual(replay["case_sha256"], report["case_sha256"])
        path = self.root / "results.csv"
        path.write_text(path.read_text().replace("82.0", "83.0"))
        self.assertNotEqual(self.run_case()["sources"]["results"]["sha256"], before)
        self.assertEqual(json.loads((out / "report.json").read_text(encoding="utf-8"))["sources"]["results"]["sha256"], before)

    def test_cli_exit_codes_and_no_overwrite(self):
        out = self.root / "output"
        cmd = [sys.executable, str(SCRIPT), "audit", str(self.root / "case.json"), "--out", str(out)]
        result = subprocess.run(cmd + ["--fail-on-inconsistency"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue((out / "report.html").is_file())
        saved = (out / "report.html").read_bytes()
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual((out / "report.html").read_bytes(), saved)
        cmd[-1] = str(self.root / "normal")
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_bad_quote_does_not_create_partial_report(self):
        self.case["claims"][0]["statement"]["start"] = 0
        (self.root / "case.json").write_text(json.dumps(self.case))
        out = self.root / "bad-output"
        result = subprocess.run([sys.executable, str(SCRIPT), "audit", str(self.root / "case.json"), "--out", str(out)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(out.exists())

    def test_install_copies_self_contained_skill_without_overwrite(self):
        target = installer.install(self.root)
        self.assertTrue((target / "SKILL.md").is_file())
        self.assertTrue((target / "references/case-format.md").is_file())
        result = subprocess.run([sys.executable, str(target / "scripts/papercourt.py"), "audit", str(self.root / "case.json"), "--out", str(self.root / "installed-output")], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.assertRaisesRegex(ValueError, "already exists"):
            installer.install(self.root)


if __name__ == "__main__":
    unittest.main()
