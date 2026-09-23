#!/usr/bin/env python3
"""Check skill discovery metadata, local documentation links, and demo replay."""

import importlib.util
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def check():
    skill = ROOT / "skills/papercourt"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    assert frontmatter, "SKILL.md frontmatter missing"
    metadata = dict(line.split(":", 1) for line in frontmatter[1].splitlines() if ":" in line)
    assert metadata["name"].strip() == skill.name, "Skill name must match its folder"
    assert 0 < len(metadata["description"].strip()) <= 1024, "Invalid description length"
    assert metadata["license"].strip() == "MIT", "Missing package license"
    assert len(text.splitlines()) < 200, "Keep the entry point concise; move detail to references"
    documents = [ROOT / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md")]
    for directory in ("skills", "docs", "examples", "demo"):
        documents.extend((ROOT / directory).rglob("*.md"))
    checked = 0
    for document in documents:
        body = document.read_text(encoding="utf-8")
        for target in re.findall(r"!?\[[^\n]*?\]\(([^\s)]+)\)", body):
            if target.startswith(("https://", "http://", "#")):
                continue
            path = unquote(target.split("#", 1)[0])
            assert (document.parent / path).resolve().is_file(), f"Broken link in {document.relative_to(ROOT)}: {target}"
            checked += 1
    script = skill / "scripts/papercourt.py"
    spec = importlib.util.spec_from_file_location("papercourt", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="PaperCourt-check-") as temporary:
        fresh = Path(temporary) / "report"
        module.write_report(module.audit(ROOT / "examples/tiny-ml/case.json"), fresh)
        expected = ROOT / "demo"
        paths = sorted(path.relative_to(expected) for path in expected.rglob("*") if path.is_file())
        assert paths == sorted(path.relative_to(fresh) for path in fresh.rglob("*") if path.is_file()), "Demo file list differs"
        for relative in paths:
            assert (fresh / relative).read_bytes() == (expected / relative).read_bytes(), f"Demo is stale: {relative}"
    print(f"Skill metadata, {checked} local links, and byte-identical demo replay passed.")


if __name__ == "__main__":
    check()
