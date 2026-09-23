# Validation of the 0.1.0 candidate

Validated locally on Windows with Python 3.11.5 and Codex CLI 0.147.0.

## Deterministic behavior

`python -m unittest discover -s tests -v` passes 28 tests. Coverage includes:

- Correct values, a numeric discrepancy, relative percent versus absolute
  difference, ratios, means, and a decimal tolerance boundary.
- Correct arithmetic alongside different hardware conditions; missing controls
  and missing result values remain unknown.
- Ambiguous row selectors, stale quotes, duplicate keys/headers, wrong field
  types, ragged CSV, nonfinite numbers, source path escapes, and portable
  identifier collisions are rejected.
- Multiline CSV locations, JSON decimal precision, UTF-8 BOM text, and LaTeX
  treated as text without executing includes.
- Escaped untrusted HTML, internal evidence links, retained hashes, original
  input bytes, report replay, CLI exits, and refusal to overwrite outputs.
- A copied project installation can run independently of the source skill.

The worked case has six claims and four numeric checks. It produces one numeric
discrepancy and one differing comparison. The distribution-shift assessment is
unknown. These expected results are properties of a deliberately constructed
fixture, not a measurement of review accuracy.

## Independent workflow check

A separate skill-guided review received only the skill and the three raw example
files, without the prepared case, report, or expected answers. It independently
selected eight claims and generated a valid report on its first audit run.
It recovered the numeric discrepancy, hardware difference, qualified supported
claims, and unknown distribution-shift support. Its quotes, hashes,
calculations, and evidence links were checked independently.

That review revealed an apostrophe escaping defect in Markdown output. The
renderer was corrected, and the affected independently authored case was rerun
and rendered to verify the fix. This is one functional workflow trial. There
was no matched model-versus-ordinary-prompt experiment, expert ground-truth
benchmark, real-paper evaluation, or statistically powered quality study.

## Host and report checks

The project installer was run into `.agents/skills/papercourt`. The actual local
Codex app-server `skills/list` API identified the skill as repository-scoped and
enabled, with the expected metadata. This discovery test used an isolated
temporary runtime because the sandbox prevented initialization of the user's
existing runtime database. It did not modify global configuration or require
credentials. It verifies discovery; automatic invocation selection is untested.

The standalone HTML example was opened in a browser. The numeric discrepancy
card was visually inspected, and clicking its operand evidence link navigated
to and highlighted the correct CSV row. Structural tests check all internal
HTML link targets. Browser interaction coverage is limited to these smoke
checks, not a comprehensive accessibility or cross-browser audit.

The GitHub Actions matrix is present but has not run remotely. Python 3.10,
Python 3.12, Linux, other hosts, arbitrary PDF input, and large real-world papers
are not claimed as locally verified. The script's declared Python minimum is
3.10; the observed local runtime was 3.11.5.
