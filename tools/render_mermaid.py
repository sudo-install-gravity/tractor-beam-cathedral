#!/usr/bin/env python3
"""Render the paper's Mermaid diagrams (Figs 1-2) to PNG.

    .venv\\Scripts\\python.exe tools\\render_mermaid.py

Figures 3-7 come from ``tools/run_campaign.py``; Figures 1 and 2 are diagrams no
code produces, authored as Mermaid inside ``docs/paper/nature-draft.md``. Mermaid
renders natively on GitHub, so the ``.md`` needs nothing -- but Word does not,
so ``tools/build_paper_docx.py`` embeds these PNGs instead of shipping diagram
source into the document.

Keeping the diagrams as Mermaid *in the manuscript* rather than as binary-only
figures is deliberate: Fig. 1 asserts the package dependency graph, and a reader
who doubts it can read the twenty lines that draw it rather than trusting a
picture. The PNG is a derived artifact.

Dependency: ``@mermaid-js/mermaid-cli`` via ``npx``, which needs Node and will
download a headless browser on first use. Not a project dependency; the
committed PNGs mean nobody needs this unless they change a diagram.

Exit codes: 0 = rendered, 1 = mermaid-cli unavailable or a diagram failed.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path("docs/paper/nature-draft.md")
OUTDIR = Path("docs/paper/campaign")

#: Block order in the manuscript -> output filename. Explicit rather than
#: inferred, so inserting a third diagram fails loudly here instead of silently
#: overwriting fig2.
OUTPUTS = ["fig1_architecture.png", "fig2_provenance.png"]


def main() -> int:
    if shutil.which("npx") is None:
        print("npx not found -- Node is required to render Mermaid.", file=sys.stderr)
        return 1
    if not SRC.exists():
        print(f"missing {SRC} -- run from the repository root", file=sys.stderr)
        return 1

    blocks = re.findall(r"```mermaid\n(.*?)\n```", SRC.read_text(encoding="utf-8"), re.S)
    if len(blocks) != len(OUTPUTS):
        print(
            f"found {len(blocks)} mermaid blocks but OUTPUTS names {len(OUTPUTS)}. "
            "Update OUTPUTS -- guessing which diagram is which is exactly the "
            "silent-mismatch this list exists to prevent.",
            file=sys.stderr,
        )
        return 1

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for block, name in zip(blocks, OUTPUTS, strict=True):
            mmd = Path(tmp) / (name.replace(".png", ".mmd"))
            mmd.write_text(block, encoding="utf-8")
            dest = OUTDIR / name
            result = subprocess.run(
                [
                    "npx",
                    "--yes",
                    "@mermaid-js/mermaid-cli@11",
                    "-i",
                    str(mmd),
                    "-o",
                    str(dest),
                    "-b",
                    "white",
                    "-s",
                    "2",
                ],
                capture_output=True,
                text=True,
                shell=True,
            )
            if result.returncode != 0 or not dest.exists():
                print(f"FAILED {name}:\n{result.stderr[-800:]}", file=sys.stderr)
                return 1
            print(f"  wrote {dest}  ({dest.stat().st_size // 1024} KB)")
    print(f"\nrendered {len(OUTPUTS)} diagrams into {OUTDIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
