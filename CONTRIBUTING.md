# Contributing to PaperCourt

Useful contributions improve evidence traceability, arithmetic correctness,
installation, or the clarity of a falsifying check. A reproducible small case
is more useful than a broad review score.

## Development

Use Python 3.10 or newer. No runtime dependencies are required.

```text
python -m unittest discover -s tests -v
python tools/check_repository.py
```

For behavioral changes, include a failing case and the expected observable
result. Test missing and ambiguous evidence as well as the normal path. Keep
the skill self-contained under `skills/papercourt`; host-specific metadata must
not make the Python helper depend on that host.

## Evidence and examples

- Use original synthetic material or material whose redistribution license is
  documented. Do not submit private manuscripts, reviewer correspondence, or
  unpublished experimental data.
- Preserve exact quotes and locations. A supplied source is not automatically
  authentic, and a matching number is not proof of a scientific claim.
- Keep deterministic checks separate from model analysis. Missing evidence
  remains unknown; proposed experiments remain unrun.
- Document units, tolerance, comparison controls, and the observable falsifier.
  Do not claim improved review quality without a suitable independent evaluation.

## Pull requests

Explain the concrete behavior that changes and include verification evidence.
Keep unrelated formatting and generated files out of the change. If report
rendering or the worked case changes, regenerate the demonstration into a new
directory and compare it before updating `demo/`:

```text
python skills/papercourt/scripts/papercourt.py audit examples/tiny-ml/case.json --out output/updated-demo
```

Treat schema changes as compatibility changes. Describe migrations before
changing accepted case fields or exit-code semantics. Contributions are
distributed under the [MIT license](LICENSE).

## Releases

From a clean committed checkout, run:

```text
python tools/build_release.py --out output/release
```

This creates source and standalone skill archives plus SHA-256 checksums.
Verify installation and a sample audit from the extracted archive. Publication
is a separate maintainer action; the build script never pushes or publishes.
