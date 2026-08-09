#!/usr/bin/env python3
"""Build an editable .docx of the threat-population literature survey.

    .venv\\Scripts\\python.exe tools\\build_survey_docx.py

A plain pandoc conversion — this file has no figures and no "Non-expert
summary" callouts, unlike the main manuscript, so it needs none of the
custom-style machinery ``tools/build_paper_docx.py`` carries for those —
plus two fixes from ``tools/_docx_post.py``, shared with that script:

1. **Page numbers.** Pandoc's default reference document has no footer
   at all. ``build_reference_docx`` builds one with a page-number footer
   wired in, used here with no extra paragraph styles.
2. **Table-of-contents placement.** Pandoc's ``--toc`` places the TOC
   *before* the title heading when the title comes from the markdown's
   first ``#`` line rather than YAML metadata, which is how this file is
   written. ``move_toc_after_title`` moves it to the expected place:
   title, then contents, then body.

Dependency: pandoc, via the self-contained ``pypandoc_binary`` wheel. See
``tools/build_paper_docx.py`` for install instructions; it is not
duplicated here.

Exit codes: 0 = built, 1 = missing dependency or conversion failure.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from _docx_post import build_reference_docx, move_toc_after_title

SRC = Path("docs/paper/threat-population-survey.md")
OUT = Path("docs/paper/threat-population-survey.docx")


def main() -> int:
    try:
        import pypandoc
    except ImportError:
        print(
            "pypandoc not installed. This is an authoring tool, not a project dependency:\n"
            "    .venv\\Scripts\\python.exe -m pip install pypandoc_binary",
            file=sys.stderr,
        )
        return 1

    if not SRC.exists():
        print(f"missing {SRC} -- run from the repository root", file=sys.stderr)
        return 1

    pandoc = pypandoc.get_pandoc_path()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        pypandoc.convert_file(
            str(SRC),
            "docx",
            outputfile=str(OUT),
            extra_args=[
                "--reference-doc",
                str(build_reference_docx(pandoc, work)),
                "--toc",
                "--toc-depth=3",
                "--standalone",
            ],
        )

    move_toc_after_title(OUT)

    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
