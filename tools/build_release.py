#!/usr/bin/env python3
"""Build deterministic archives from a clean committed checkout; never publish."""

import argparse
import hashlib
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def archive(path, entries):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, content in sorted(entries):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(out):
    if git("status", "--porcelain").strip():
        raise ValueError("Release builds require a clean committed checkout")
    out = Path(out).resolve()
    if out.exists():
        raise ValueError("Choose a new output directory; release builds never overwrite")
    paths = git("ls-tree", "-r", "--name-only", "HEAD").decode().splitlines()
    files = {path: git("show", f"HEAD:{path}") for path in paths}
    version = re.search(rb'^VERSION = "(\d+\.\d+\.\d+)"$', files["skills/papercourt/scripts/papercourt.py"], re.M)[1].decode()
    source_name = f"PaperCourt-{version}.zip"
    skill_name = f"papercourt-skill-{version}.zip"
    out.mkdir(parents=True)
    archive(out / source_name, [(f"PaperCourt-{version}/{name}", data) for name, data in files.items()])
    skill_files = [(name.removeprefix("skills/"), data) for name, data in files.items() if name.startswith("skills/papercourt/")]
    archive(out / skill_name, skill_files)
    hashes = [f"{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}" for name in (source_name, skill_name)]
    (out / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="ascii", newline="\n")
    print(f"Built {source_name}, {skill_name}, and SHA256SUMS from {git('rev-parse', '--short', 'HEAD').decode().strip()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.out)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Build error: {exc}\n")


if __name__ == "__main__":
    main()
