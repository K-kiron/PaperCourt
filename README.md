# PaperCourt

**Put a paper's strongest claims in front of its evidence.**

An installable skill for auditing empirical machine-learning papers. PaperCourt
connects claims to exact source quotes and result rows, recomputes numbers,
exposes changed comparison conditions, and proposes small tests that could
falsify a claim. Every report separates script checks from model analysis.

> **Abstract:** "Improves accuracy across all image datasets and compute budgets."
>
> **Supplied evidence:** One dataset. One training budget.
>
> **Next check:** A controlled low-budget comparison, with a predeclared outcome
> that would contradict the universal claim.

[Read the example report](demo/report.md) · [Open the skill](skills/papercourt/SKILL.md) · [Case format](skills/papercourt/references/case-format.md)

## Try the reproducible demo

Requires **Python 3.10+**. The helper uses only the standard library. No API key,
package installation, or network access is needed to replay the example.

From the downloaded or cloned repository:

```text
python skills/papercourt/scripts/papercourt.py audit examples/tiny-ml/case.json --out output/first-review
```

Open `output/first-review/report.html` in a browser. It is a standalone report
with source links and highlighted evidence lines. The checked-in
[HTML demonstration](demo/report.html) is the same format; download it or open
it locally, since GitHub displays HTML source rather than executing it.

| Paper claim | Script check | Model analysis |
| --- | --- | --- |
| 82.0% accuracy in the stated setting | Consistent with the supplied aggregate | Supported within that scope |
| 5.0 percentage-point gain | 82.0 − 80.0 = **2.0**, not 5.0 | Conflicting supplied evidence |
| 2.0× faster under identical hardware | Ratio is 2.0; **CPU and GPU differ** | Confounded comparison |
| Improvement across every dataset and budget | No automatic semantic judgment | Scope exceeds the one tested setting |
| Robustness under distribution shift | No shift result supplied | **Unknown**, not false |
| 2.5% relative accuracy gain | 100 × (82 − 80) / 80 = **2.5%** | Supported for the stated setting |

The example is original fictional teaching material under MIT, not a real
experiment. Its prepared case replays a worked review; it does not demonstrate
automatic claim extraction or improved review quality.

## Install the skill in Codex

Install into the project containing your paper:

```text
python tools/install_skill.py --project "C:/path/to/paper-project"
```

The installer copies the self-contained `skills/papercourt` directory to
`<project>/.agents/skills/papercourt`. It refuses to overwrite an existing skill
and makes no global configuration changes. Alternatively, copy the folder to
that location yourself. Back up an existing installation before replacing it.

Open that project in Codex, then invoke:

```text
Use $papercourt to audit paper.md against results.csv and runtime.json.
Focus on the abstract's main empirical claims. Create a linked evidence
report with minimal falsifying checks in a local review directory.
```

Repository skill discovery follows the [official Codex skill locations](https://developers.openai.com/codex/skills).
If it does not appear, restart the host. Project discovery was verified with
Codex CLI 0.147.0 on Windows. A skill-guided workflow was also completed from
raw example inputs. Other hosts and automatic skill selection have not been
validated. The helper can be run directly without an agent host.

## What you receive

- **Claim → evidence → support → limitation → next check**, with exact paper
  quotes, physical CSV lines, and JSON record pointers.
- **Repeatable arithmetic:** values, differences, relative changes, ratios,
  and unweighted means, with explicit absolute tolerances.
- **Comparison checks:** dataset, split, metric, unit, protocol, and additional
  controls selected by the reviewer. Missing controls stay unknown.
- **Reviewable outputs:** Markdown, standalone HTML, and structured JSON.
- **Replayable evidence:** SHA-256 hashes and byte-preserved inputs. Rerun the
  case under a report's `inputs/` directory to reproduce its checks.

The agent reads the materials, selects claims, writes their evidence mapping,
and supplies the semantic assessment. The Python helper checks those mappings
and calculations. It does not automatically interpret a paper or certify that
the mapping entails the claim. Every semantic assessment is labeled model
analysis and includes a proposed check and observable falsifier.

## Use your own evidence

Supply Markdown, LaTeX source, or extracted plain text, together with CSV or a
JSON array of result records. Keep sources inside the review case directory.
The [case format](skills/papercourt/references/case-format.md) documents all
required fields and gives a minimal example. You can author a case manually or
have the skill prepare it from the supplied material.

```text
python skills/papercourt/scripts/papercourt.py audit path/to/case.json --out output/my-review
```

Output directories must be new. A normal exit code of `0` means the report was
created, not that all claims are supported. Add `--fail-on-inconsistency` to
return `1` for a numeric discrepancy or differing selected conditions. Invalid
inputs return `2`. Unknowns and semantic assessments do not trigger that flag.

## Scope and privacy

PaperCourt currently targets empirical ML papers. It does not parse arbitrary
PDF layouts, resolve LaTeX includes, verify the literature, run experiments,
execute supplied code, infer significance, or decide whether a paper is valid.
JSON links identify the record pointer within a whole-file snapshot; precise
JSON source-line extraction is not implemented. Matching selected metadata
does not prove the absence of unrecorded confounders.

The helper is local and makes no network calls. **Using a hosted agent still
processes supplied text under that host's data policy.** The skill does not
authorize additional uploads or publication. Reports copy all declared source
files; keep private reviews outside public repositories and inspect their
contents before sharing.

Missing evidence is not a refutation. Model assessments, numeric mappings,
units, tolerance choices, and proposed experiments need human review. No claim
of better review accuracy, time savings, or scientific validity has been
established by this initial example.

## Verify the implementation

```text
python -m unittest discover -s tests -v
```

The suite covers real files and CLI behavior, including stale quotes, ambiguous
rows, missing controls, exact decimal boundaries, malformed inputs, source
replay, installation, HTML escaping, and link targets. See
[validation notes](docs/validation.md) for the tested environment and limits.
The CI matrix is configured for Windows and Linux with Python 3.10 and 3.12;
remote CI has not yet run for this local release candidate.

## Related work

The [verify-claims skill in research-paper-lifecycle-skills](https://github.com/ShaishavMaisuria/research-paper-lifecycle-skills/blob/main/skills/verify-claims/SKILL.md)
is a related claim-review workflow. PaperCourt focuses this first version on
replayable numeric checks, inspectable source snapshots, explicit comparison
conditions, and testable counterexamples. Its code, instructions, and teaching
example are original; no implementation or skill text is copied from that project.

## License

[MIT](LICENSE), including the original fictional examples. Version 0.1.0 is a
local release candidate; no public release or hosted service is implied.
