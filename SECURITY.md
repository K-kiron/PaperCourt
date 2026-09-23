# Reporting security problems

PaperCourt reads local text and result files and writes reports containing the
declared inputs. It does not execute paper code or make network requests.
Agent-host processing and any installer network access are separate from the
report helper.

Do not attach private papers, credentials, sensitive paths, or unpublished data
to a public report. Use a minimal synthetic reproducer. For a potentially
sensitive vulnerability, open an issue requesting a private contact without
including exploit details or sensitive information; a maintainer can arrange
the next step. This repository does not promise a response-time SLA.

Include the PaperCourt version, operating system, Python version, and expected
versus observed behavior when it is safe to do so. Security fixes target the
latest published version.
