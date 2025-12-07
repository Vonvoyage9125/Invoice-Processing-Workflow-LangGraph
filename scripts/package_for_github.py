#!/usr/bin/env python3
"""
Create a GitHub-ready package of the repository under ./Github

Rules:
- Exclude runtime artifacts and sensitive files: demo.db, logs/, artifacts/, recordings, .env* files
- Exclude caches: __pycache__, .pytest_cache, *.pyc
- Preserve directory structure and file timestamps

After running, the `Github/` folder will contain a copy safe to upload to GitHub.
"""
import shutil
from pathlib import Path
import fnmatch
import os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Github'

# Patterns to exclude (relative paths or glob patterns)
EXCLUDE_DIRS = {
    'logs', 'artifacts', '.pytest_cache', '__pycache__', '.vscode', '.venv', 'dist', 'build'
}

EXCLUDE_FILES = [
    'demo.db',
]

EXCLUDE_GLOBS = [
    '.env*',
    '*.pyc',
    '*.log',
    '*.sqlite',
    '*.db',
    'recording.mp4',
    'voice.wav',
]


def should_exclude(path: Path) -> bool:
    # Exclude if any parent folder is in EXCLUDE_DIRS
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    # Exclude specific filenames
    if path.name in EXCLUDE_FILES:
        return True
    # Exclude globs
    for pat in EXCLUDE_GLOBS:
        if fnmatch.fnmatch(path.name, pat):
            return True
    return False


def copy_repo():
    if OUT.exists():
        print('Removing existing', OUT)
        shutil.rmtree(OUT)
    print('Creating', OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    for src in ROOT.iterdir():
        # skip the output folder itself
        if src == OUT:
            continue
        rel = src.relative_to(ROOT)
        if should_exclude(rel):
            print('Excluding', rel)
            continue
        dest = OUT / rel
        if src.is_dir():
            # copy tree but filter
            def ignore_func(dir, contents):
                ignored = []
                for name in contents:
                    p = Path(dir) / name
                    relp = p.relative_to(ROOT)
                    if should_exclude(relp):
                        ignored.append(name)
                return set(ignored)

            shutil.copytree(src, dest, ignore=ignore_func)
        else:
            # file
            if should_exclude(rel):
                print('Excluding', rel)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    print('Package created at', OUT)


if __name__ == '__main__':
    copy_repo()
