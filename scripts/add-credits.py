#!/usr/bin/env python3
"""Add credit to all non-.md source files that don't have it yet."""
import os

AUTHOR = "Tech127x"
URL = "https://github.com/Tech127x/volume-monitor"
PY_CREDIT = f"# Volume Monitor — {URL}\n# Copyright (c) 2025 {AUTHOR}\n\n"
SH_CREDIT = f"# Volume Monitor — {URL}\n# Copyright (c) 2025 {AUTHOR}\n"

SKIP = {".git", "__pycache__", "node_modules"}
ALREADY = {"__init__.py", "conftest.py", "setup.py"}

for root, dirs, files in os.walk("."):
    parts = root.split(os.sep)
    if any(x in SKIP for x in parts):
        continue
    for f in files:
        if f.endswith((".md", ".svg")):
            continue
        path = os.path.join(root, f)
        try:
            with open(path) as fh:
                content = fh.read()
        except Exception:
            continue
        if "Tech127x" in content:
            continue
        if f.endswith(".py"):
            if f in ALREADY:
                continue
            if content.startswith('"""'):
                idx = content.index('"""') + 3
                end = content.index('"""', idx) + 3
                content = content[:end] + "\n" + PY_CREDIT + content[end:].lstrip("\n")
            elif content.startswith("'''"):
                idx = content.index("'''") + 3
                end = content.index("'''", idx) + 3
                content = content[:end] + "\n" + PY_CREDIT + content[end:].lstrip("\n")
            else:
                content = PY_CREDIT + content
        elif f.endswith((".sh", ".fish")):
            if content.startswith("#!"):
                nl = content.index("\n")
                content = content[: nl + 1] + "\n" + SH_CREDIT + content[nl + 1 :].lstrip("\n")
            else:
                content = SH_CREDIT + content
        elif f.endswith(".js"):
            content = f"// Volume Monitor — {URL}\n// Copyright (c) 2025 {AUTHOR}\n\n" + content
        elif f.endswith(".service") or f == "Makefile" or f == ".gitignore":
            content = SH_CREDIT + content
        else:
            continue
        with open(path, "w") as fh:
            fh.write(content)
        print(path)

