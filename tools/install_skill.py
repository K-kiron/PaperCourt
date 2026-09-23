#!/usr/bin/env python3
"""Copy PaperCourt into one project's Codex skill directory without overwriting."""

import argparse
import shutil
from pathlib import Path


def install(project):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError("The target project directory must already exist")
    source = Path(__file__).resolve().parents[1] / "skills" / "papercourt"
    parent = project / ".agents" / "skills"
    if not parent.resolve().is_relative_to(project):
        raise ValueError("The skill directory must stay inside the target project")
    destination = parent / "papercourt"
    if destination.exists() or destination.is_symlink():
        raise ValueError("PaperCourt already exists in this project; no files were changed")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    try:
        destination = install(args.project)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Installation error: {exc}\n")
    print(f"Installed: {destination}")
    print("Open this project in Codex and invoke $papercourt. Restart if it is not listed.")


if __name__ == "__main__":
    main()
