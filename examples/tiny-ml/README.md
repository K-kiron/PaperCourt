# Tiny ML example

All paper prose, model names, datasets, numbers, and review mappings in this
directory are original fictional teaching material, covered by the repository's
MIT license. They do not describe real research, people, or measured performance.
No private paper, external dataset, or third-party prose is included.

`case.json` is an explicit worked review mapping. Its semantic assessments are
illustrative model analysis. Rerunning it replays arithmetic and location checks;
it is not a fresh model evaluation and does not validate claim extraction.

| Claim | Purpose | Expected evidence |
| --- | --- | --- |
| C1 | Scope overreach | One dataset and one budget cannot establish all settings |
| C2 | Correct qualified number | 82.0 agrees with the supplied aggregate |
| C3 | Numeric inconsistency | 82.0 - 80.0 = 2.0, not 5.0 percentage points |
| C4 | Different comparison conditions | 20 / 10 = 2.0, but CPU and GPU differ |
| C5 | Missing evidence | Distribution-shift support stays unknown |
| C6 | Correct relative number | 100 × (82.0 - 80.0) / 80.0 = 2.5% |

Reproduce from the repository root:

```text
python skills/papercourt/scripts/papercourt.py audit examples/tiny-ml/case.json --out output/tiny-ml
```

Open `output/tiny-ml/report.html`. Click any evidence link to jump to its source
line. Use a new output directory on subsequent runs. The checked-in
[Markdown demonstration](../../demo/report.md) is generated from this case.
