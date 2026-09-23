# Case format, version 1

The host agent extracts claims and writes this mapping. The helper verifies
locations, arithmetic, and selected metadata. Semantic assessments are supplied
by the agent and remain explicitly labeled `model_analysis` in all reports.

## Inputs

Use UTF-8. Source files must be inside the case file's directory, including
subdirectories. Absolute paths, parent traversal, and escaping symlinks are
rejected. Files are limited to 5 MB each. Markdown, LaTeX, and extracted text are
read as text; includes, macros, citations, PDF extraction, and code execution are
not resolved. CSV has a header row. JSON results are an array of record objects.
Use unambiguous scalar fields and a stable row ID. Nested JSON results need an
explicit local conversion, preserving a reference to the original material.

```json
{
  "version": 1,
  "title": "Example evidence review",
  "sources": {"paper": "paper.md", "results": "results.csv"},
  "claims": [{
    "id": "C1",
    "statement": {
      "source": "paper", "start": 5, "end": 5,
      "quote": "The reported accuracy is 82.0%."
    },
    "numeric": [{
      "operation": "value",
      "operands": [{"source": "results", "row": {"id": "method"}, "field": "value"}],
      "expected": "82.0", "tolerance": "0.05", "unit": "percent",
      "conditions": []
    }],
    "assessment": {
      "status": "supported_within_scope",
      "reason": "The sentence agrees with the supplied aggregate result.",
      "evidence": [{"source": "results", "row": {"id": "method"}}],
      "limitations": "The supplied aggregate does not establish uncertainty.",
      "next_check": "Recompute this aggregate from the per-seed evaluation logs.",
      "falsifier": "The recomputed aggregate differs from 82.0 by more than 0.05 percentage points."
    }
  }]
}
```

Top-level keys are required. Unknown fields are rejected. Claim/source IDs start
with an ASCII letter and contain only letters, digits, underscores, and hyphens.
Claim and source IDs must be unique ignoring case; source IDs cannot be Windows
device names such as `CON` or `AUX`. Every claim needs all the shown fields; `numeric`
may be empty. Sources must exist; a missing file is a specification error, while
a missing result row or value produces an `unknown` numeric outcome.

## Evidence references

- Text: `source`, `start`, `end`, `quote`. Lines are one-based and inclusive.
  The exact nonempty quote must occur within that span. Newlines are normalized
  when reading. This detects stale quotes, not whether a quote entails a claim.
- Result: `source`, `row`, optional `field`. `row` is a nonempty exact-match
  selector, such as `{"id": "method", "split": "test"}`. Numeric JSON values
  and selector values are compared as strings. Missing selections are unknown;
  multiple matches are an error. No implicit "first row" or row aggregation.
- CSV references preserve the full physical line span of multiline records.
  JSON references record the array pointer (for example `/2`) and link to the
  complete JSON snapshot. JSON line precision beyond the file is not claimed.

`assessment.evidence` lists the material behind the semantic assessment. A
non-unknown assessment needs at least one located reference. The script cannot
prove that the chosen reference justifies the assessment. Source hashes are
provenance identifiers, not authenticity certificates. A report contains all
declared source text, including material that was not cited.

## Numeric checks

Every check requires `operation`, `operands`, `expected`, `tolerance`, `unit`, and
`conditions`. Each operand selects one result record and one `field`.

| Operation | Calculation | Operands |
| --- | --- | --- |
| `value` | a | 1 |
| `difference` | a - b | 2 |
| `relative_change` | 100 × (a - b) / b | 2 |
| `ratio` | a / b | 2 |
| `mean` | arithmetic mean of supplied values | 1 or more |

Calculations use decimal arithmetic (50 significant digits). `expected` and
nonnegative `tolerance` are explicit absolute values. The outcome is
`consistent` when `abs(actual - expected) <= tolerance`, otherwise
`inconsistent`. A nonpositive denominator for ratios/relative change is
`unknown`. NaN, infinity, booleans, unit-bearing strings such as `"82%"`, and
numeric exponents beyond ±100 are invalid; normalize values explicitly first.

No automatic unit conversion is performed. An accuracy recorded on a 0–100
scale produces percentage points under `difference`; `relative_change` returns
percent. For a 0–1 input scale, `difference` stays on that scale. `unit` labels
the output, and its semantic correctness must be checked by the reviewer.
For speedup, use baseline time as `a` and method time as `b`. The helper does
not infer whether larger or smaller is better.

For every multi-operand check, `conditions` must include `dataset`, `split`,
`metric`, `unit`, and `protocol`. Add relevant controls such as `budget`,
`hardware`, `batch_size`, `precision`, `seeds`, or `aggregation`. Values are
read from the selected records. A missing field yields `unknown`; an observed
difference yields `different` even if other fields are missing. All supplied
fields matching yields `aligned`, which makes no claim about omitted controls.
Single-operand checks have `not_applicable` comparison status.

For a mean across seeds, seed is intentionally the varying factor; check the
fixed controls and describe the seed coverage in limitations. Means are
unweighted. Weighted aggregation and uncertainty tests require separate,
explicit analysis. Arithmetic results remain visible when conditions differ;
do not describe those results as a validated performance advantage.

## Model analysis

`assessment.status` is one of:

- `supported_within_scope`: the cited evidence supports this qualified claim.
- `limited`: the evidence covers less scope, or the comparison has confounders.
- `conflicting_evidence`: identified supplied evidence conflicts with the claim.
- `unknown`: supplied material does not establish support or conflict.

These statuses are never calculated by the helper. Even an arithmetically
consistent result can have a limited semantic assessment. Each assessment also
requires `reason`, `limitations`, `next_check`, and `falsifier`, all nonempty
strings. Next checks are proposals, not reported experimental results. Name the
smallest useful control and the observable outcome that would challenge the
claim. A broad claim often needs only one valid counterexample to fail, but a
few successful extra runs do not establish a universal claim.

## Running and sharing

```text
python <skill>/scripts/papercourt.py audit case.json --out new-report
```

Outputs are `report.md`, a standalone `report.html`, `report.json`, Markdown
source snapshots under `evidence/`, and byte-preserved case/source files under
`inputs/`. Rerun the case in `inputs/` to replay a report independently of the
original working directory. HTML needs no server, JavaScript, fonts, or
external assets. Keep the Markdown report with its `evidence` folder; HTML is
self-contained for reading; the complete folder also preserves original bytes
for hash verification and replay. Displayed text normalizes newlines and removes
UTF-8 BOMs. Reports never overwrite an existing directory. Keep private
reports outside public repositories and review the copied material before
sharing. The helper performs no network calls; the host agent's own processing
and data policy still apply.

Exit codes: `0` report created (findings may exist), `2` invalid input or I/O
failure. With `--fail-on-inconsistency`, `1` means at least one numeric mismatch
or differing selected comparison condition, and the report is still written.
Unknowns and model assessments do not trigger that flag. Exit `0` is not a
clean bill of health. A missing or malformed source prevents report generation;
declare only files actually supplied and record absent evidence as unknown.
