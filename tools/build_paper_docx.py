#!/usr/bin/env python3
"""Build an editable .docx of the paper draft for LibreOffice / Word.

    .venv\\Scripts\\python.exe tools\\build_paper_docx.py

Why this exists rather than a bare ``pandoc in.md -o out.docx``: three things the
default conversion does not give us.

1. **The per-paragraph "Non-expert summary" notes get their own named paragraph
   style** (``NonExpertSummary``). They survive the round trip, they are visually
   distinct, and — because they are a *named style* — a reviewer can restyle or
   delete all of them in one operation. That matters: they are drafting aids and
   must be stripped before journal submission.
2. **Every figure legend gets a bordered placeholder frame above it**
   (``FigurePlaceholder``), so there is an obvious slot to drop a diagram into.
3. A table of contents, because the draft is ~1,500 lines — **placed after the
   title**, not before it. Pandoc's own ``--toc`` puts the TOC first in the
   document body when the title comes from the markdown's first ``#`` line
   rather than YAML metadata (the case here), which reads as contents-before-
   cover-page. ``tools/_docx_post.py:move_toc_after_title`` fixes the order
   after pandoc runs; see that module for why this needs post-processing
   rather than a pandoc flag.
4. **Page numbers**, centered in the footer — pandoc's default reference
   document has none. ``tools/_docx_post.py:build_reference_docx`` builds a
   reference doc with a page-number footer wired in (and injects the two
   custom styles above into the same reference doc); see that module for
   why this has to be an input to pandoc rather than output post-processing.

Dependency: pandoc, via the self-contained ``pypandoc_binary`` wheel. It is
deliberately **not** a project dependency — nothing in ``src/`` needs it and this
is a one-off authoring tool. Install it where you like::

    .venv\\Scripts\\python.exe -m pip install pypandoc_binary

Exit codes: 0 = built, 1 = missing dependency or conversion failure.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from _docx_post import build_reference_docx, move_toc_after_title

SRC = Path("docs/paper/nature-draft.md")
OUT = Path("docs/paper/nature-draft.docx")

SUMMARY_STYLE = "NonExpertSummary"
PLACEHOLDER_STYLE = "FigurePlaceholder"

# Injected into the reference doc's styles.xml. w:name is what pandoc matches on.
STYLE_XML = f"""
<w:style w:type="paragraph" w:customStyle="1" w:styleId="{SUMMARY_STYLE}">
  <w:name w:val="{SUMMARY_STYLE}"/><w:basedOn w:val="BodyText"/><w:qFormat/>
  <w:pPr>
    <w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="4A7EBB"/></w:pBdr>
    <w:shd w:val="clear" w:color="auto" w:fill="EEF3FA"/>
    <w:spacing w:before="120" w:after="200"/><w:ind w:left="340" w:right="170"/>
  </w:pPr>
  <w:rPr><w:i/><w:color w:val="1F3864"/><w:sz w:val="19"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:customStyle="1" w:styleId="{PLACEHOLDER_STYLE}">
  <w:name w:val="{PLACEHOLDER_STYLE}"/><w:basedOn w:val="BodyText"/><w:qFormat/>
  <w:pPr>
    <w:pBdr>
      <w:top w:val="dashed" w:sz="8" w:space="12" w:color="A6A6A6"/>
      <w:left w:val="dashed" w:sz="8" w:space="12" w:color="A6A6A6"/>
      <w:bottom w:val="dashed" w:sz="8" w:space="12" w:color="A6A6A6"/>
      <w:right w:val="dashed" w:sz="8" w:space="12" w:color="A6A6A6"/>
    </w:pBdr>
    <w:shd w:val="clear" w:color="auto" w:fill="F7F7F7"/>
    <w:spacing w:before="280" w:after="120" w:line="360" w:lineRule="auto"/>
    <w:jc w:val="center"/>
  </w:pPr>
  <w:rPr><w:b/><w:color w:val="808080"/><w:sz w:val="20"/></w:rPr>
</w:style>
"""

_FIG_RE = re.compile(r"^\*\*Fig\.\s*(\d+)\s*\|\s*(.+?)\*\*")
FIGURE_DIR = Path("docs/paper/campaign")


def _rendered_figure(num: str) -> Path | None:
    """The rendered PNG for figure ``num``, if the campaign has produced one."""
    hits = sorted(FIGURE_DIR.glob(f"fig{num}_*.png"))
    return hits[0] if hits else None


def preprocess(text: str) -> tuple[str, int, int]:
    """Embed rendered figures, wrap summaries in a styled Div, placeholder the rest.

    Figures that the campaign has actually rendered are **embedded**; only the
    ones with no PNG still get a "GOES HERE" frame. Mermaid fences are dropped in
    favour of their rendered image, since Word has no Mermaid renderer and would
    otherwise show the diagram source as a wall of code.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = n_sum = n_fig = 0

    while i < len(lines):
        line = lines[i]

        # Mermaid source: the rendered PNG is embedded at the legend, so drop the
        # fence rather than shipping unrenderable code into the document.
        if line.strip() == "```mermaid":
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                i += 1
            i += 1  # past the closing fence
            out += [
                f'::: {{custom-style="{PLACEHOLDER_STYLE}"}}',
                "[ diagram source omitted — see the rendered figure above. "
                "The Mermaid source lives in docs/paper/nature-draft.md and renders "
                "on GitHub; regenerate the image with tools/render_mermaid.py ]",
                ":::",
                "",
            ]
            continue

        match = _FIG_RE.match(line)
        if match:
            n_fig += 1
            num, title = match.group(1), match.group(2).rstrip(".")
            png = _rendered_figure(num)
            if png is not None:
                # Pandoc resolves the path relative to its working directory, which
                # is the repository root -- the same place this script must be run.
                out += [f"![]({png.as_posix()})", "", line]
            else:
                out += [
                    f'::: {{custom-style="{PLACEHOLDER_STYLE}"}}',
                    f"[ FIGURE {num} GOES HERE — {title} ]",
                    "",
                    "Delete this frame and Insert ▸ Image in its place.",
                    ":::",
                    "",
                    line,
                ]
            i += 1
            continue

        if line.startswith("***Non-expert summary:***"):
            n_sum += 1
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() != "":
                para.append(lines[i])
                i += 1
            out += [f'::: {{custom-style="{SUMMARY_STYLE}"}}', *para, ":::"]
            continue

        out.append(line)
        i += 1

    return "\n".join(out), n_sum, n_fig


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
        processed, n_sum, n_fig = preprocess(open(SRC, encoding="utf-8").read())
        md = work / "processed.md"
        open(md, "w", encoding="utf-8", newline="\n").write(processed)
        print(f"wrapped {n_sum} non-expert summaries; inserted {n_fig} figure placeholders")

        subprocess.run(
            [
                pandoc,
                str(md),
                "-f",
                "markdown+fenced_divs+pipe_tables+backtick_code_blocks",
                "-t",
                "docx",
                "--reference-doc",
                str(build_reference_docx(pandoc, work, extra_style_xml=STYLE_XML)),
                "--toc",
                "--toc-depth=3",
                "--wrap=none",
                "-o",
                str(OUT),
            ],
            check=True,
        )

    move_toc_after_title(OUT)

    with zipfile.ZipFile(OUT) as z:
        doc = z.read("word/document.xml").decode("utf-8")
        style_xml = z.read("word/styles.xml").decode("utf-8")
    ok = True
    embedded = doc.count("<pic:pic")
    used_sum = doc.count(f'w:val="{SUMMARY_STYLE}"')
    ok = SUMMARY_STYLE in style_xml and used_sum == n_sum
    print(
        f"  {'ok ' if ok else 'BAD'} {SUMMARY_STYLE}: defined, used {used_sum}x (expected {n_sum})"
    )
    print(f"  ok  figures embedded: {embedded} of {n_fig} legends have a rendered image")
    if embedded < n_fig:
        print(
            f"      ({n_fig - embedded} still placeholder frames -- run tools/run_campaign.py "
            "and tools/render_mermaid.py to render the rest)"
        )

    print(f"\nwrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
