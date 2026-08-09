"""Shared machinery for this project's markdown-to-.docx conversions.

Used by ``tools/build_paper_docx.py`` and ``tools/build_survey_docx.py``.
Not a project dependency, same as those two scripts — a one-off authoring
helper, not something ``src/`` needs.

Two independent fixes to pandoc's default docx output, applied at two
different stages of the pipeline:

1. **Page numbers** (``build_reference_docx``) — pandoc's default
   reference document has no header or footer at all, so output carries
   no page numbers unless the reference doc supplies them. This builds a
   reference doc, starting from pandoc's own default one, with a centered
   ``PAGE`` field wired into a real footer part (a new ``word/footer1.xml``,
   registered in ``[Content_Types].xml`` and ``word/_rels/document.xml.rels``,
   referenced from the body's ``sectPr``) — the mechanism pandoc's docx
   writer is documented to carry over from the reference doc into every
   output file, which is why building the reference doc (an input) is the
   fix, rather than post-processing the output.
2. **Table-of-contents placement** (``move_toc_after_title``) — pandoc's
   ``--toc`` places the TOC as the very first thing in the document body,
   *before* the title heading, whenever the title comes from the
   markdown's first ``#`` line rather than YAML front-matter metadata
   (the case for every document this project converts). This one **is**
   output post-processing: it moves the TOC structured-document-tag block
   to directly after the first ``Heading1`` paragraph, leaving everything
   else in the document untouched.
"""

from __future__ import annotations

import os
import re
import subprocess
import zipfile
from pathlib import Path

# --- 1. Reference-doc construction: page-number footer, optional styles -----

#: A minimal footer part: one centered paragraph reading "Page " followed by
#: a PAGE field. `xml:space="preserve"` needs no namespace declaration --
#: `xml:` is a reserved prefix, predefined by the XML spec itself.
_FOOTER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:t xml:space="preserve">Page </w:t></w:r>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="separate"/></w:r>
    <w:r><w:t>1</w:t></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>
"""

#: Relationship id for the footer part. A descriptive string, not "rIdN" --
#: OOXML relationship ids are arbitrary xsd:ID tokens, and a name specific
#: enough not to collide with whatever pandoc or Word assigns elsewhere is
#: safer than picking a number and hoping nothing else uses it.
_FOOTER_REL_ID = "rIdPageNumberFooter"

_CONTENT_TYPES_FOOTER_ENTRY = (
    '<Override PartName="/word/footer1.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
)

_DOCUMENT_RELS_FOOTER_ENTRY = (
    f'<Relationship Id="{_FOOTER_REL_ID}" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" '
    'Target="footer1.xml"/>'
)


def _add_page_number_footer(unpacked: Path) -> None:
    """Add the page-number footer part to an unpacked reference-doc tree,
    wiring it into Content_Types, document relationships, and the body's
    ``sectPr`` -- the four places OOXML requires a footer to be registered.

    Operates on files already extracted under ``unpacked`` (mutates them
    in place); does not read or write a .docx archive itself.
    """
    (unpacked / "word" / "footer1.xml").write_text(_FOOTER_XML, encoding="utf-8")

    ct_path = unpacked / "[Content_Types].xml"
    ct = ct_path.read_text(encoding="utf-8")
    if "</Types>" not in ct:
        raise RuntimeError("unexpected [Content_Types].xml -- pandoc format changed?")
    ct_path.write_text(
        ct.replace("</Types>", _CONTENT_TYPES_FOOTER_ENTRY + "</Types>"), encoding="utf-8"
    )

    rels_path = unpacked / "word" / "_rels" / "document.xml.rels"
    rels = rels_path.read_text(encoding="utf-8")
    if "</Relationships>" not in rels:
        raise RuntimeError("unexpected word/_rels/document.xml.rels -- pandoc format changed?")
    rels_path.write_text(
        rels.replace("</Relationships>", _DOCUMENT_RELS_FOOTER_ENTRY + "</Relationships>"),
        encoding="utf-8",
    )

    doc_path = unpacked / "word" / "document.xml"
    doc = doc_path.read_text(encoding="utf-8")
    if "<w:sectPr>" not in doc:
        raise RuntimeError("unexpected word/document.xml -- no <w:sectPr> to attach a footer to")
    # w:footerReference must precede w:footnotePr etc. in CT_SectPr's declared
    # child order -- inserting it as sectPr's first child satisfies that.
    footer_ref = f'<w:footerReference w:type="default" r:id="{_FOOTER_REL_ID}"/>'
    doc_path.write_text(doc.replace("<w:sectPr>", "<w:sectPr>" + footer_ref, 1), encoding="utf-8")


def build_reference_docx(pandoc: str, work: Path, extra_style_xml: str = "") -> Path:
    """Build a pandoc ``--reference-doc``: pandoc's own default reference
    document, with a page-number footer added, and optionally extra
    paragraph styles injected into ``styles.xml``.

    Parameters
    ----------
    pandoc
        Path to the pandoc executable (``pypandoc.get_pandoc_path()``).
    work
        A writable scratch directory (a ``tempfile.TemporaryDirectory()``,
        typically).
    extra_style_xml
        Raw ``<w:style>`` XML to inject before ``</w:styles>``, or ``""``
        to add none. Caller-supplied, e.g. ``build_paper_docx.py``'s
        ``NonExpertSummary``/``FigurePlaceholder`` styles.

    Returns
    -------
    Path
        The built reference .docx, inside ``work``.
    """
    ref = work / "reference.docx"
    with open(ref, "wb") as fh:
        subprocess.run(
            [pandoc, "--print-default-data-file", "reference.docx"], stdout=fh, check=True
        )

    unpacked = work / "ref"
    with zipfile.ZipFile(ref) as z:
        z.extractall(unpacked)

    _add_page_number_footer(unpacked)

    if extra_style_xml:
        styles = unpacked / "word" / "styles.xml"
        xml = styles.read_text(encoding="utf-8")
        if "</w:styles>" not in xml:
            raise RuntimeError("unexpected reference styles.xml -- pandoc format changed?")
        styles.write_text(
            xml.replace("</w:styles>", extra_style_xml + "</w:styles>"), encoding="utf-8"
        )

    out = work / "reference-custom.docx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(unpacked):
            for name in files:
                path = Path(root) / name
                z.write(path, path.relative_to(unpacked).as_posix())
    return out


# --- 2. Output post-processing: TOC placement -------------------------------

#: Pandoc emits exactly one ``w:sdt`` block for the TOC, and it is the
#: first ``w:sdt`` in the document; no nested ``w:sdt`` appears inside it.
_TOC_RE = re.compile(r"<w:sdt>.*?</w:sdt>", re.DOTALL)

#: The title heading: pandoc's ``Heading1``-styled paragraph, whatever
#: text it contains.
_HEADING1_RE = re.compile(
    r'<w:p><w:pPr><w:pStyle w:val="Heading1"\s*/></w:pPr>.*?</w:p>', re.DOTALL
)


def move_toc_after_title(docx_path: Path) -> None:
    """Rewrite ``docx_path`` in place so its table of contents follows the
    title heading instead of preceding it.

    Raises rather than silently leaving the file in its original,
    wrongly-ordered state if the expected structure — a Table-of-Contents
    ``w:sdt`` block, and a ``Heading1``-styled first paragraph — is not
    found (e.g. because pandoc's docx output format changed, or ``--toc``
    was not passed).

    Parameters
    ----------
    docx_path
        Path to an already-built .docx file. Rewritten in place.
    """
    with zipfile.ZipFile(docx_path) as z:
        names = z.namelist()
        contents = {name: z.read(name) for name in names}

    xml = contents["word/document.xml"].decode("utf-8")

    toc_match = _TOC_RE.search(xml)
    if toc_match is None or "Table of Contents" not in toc_match.group(0):
        raise RuntimeError(
            f"{docx_path}: no Table-of-Contents w:sdt block found in word/document.xml "
            "-- was --toc passed to pandoc, or has pandoc's docx output format changed?"
        )
    toc_block = toc_match.group(0)
    without_toc = xml[: toc_match.start()] + xml[toc_match.end() :]

    heading_match = _HEADING1_RE.search(without_toc)
    if heading_match is None:
        raise RuntimeError(
            f"{docx_path}: no Heading1 paragraph found to place the table of contents after"
        )

    insert_at = heading_match.end()
    new_xml = without_toc[:insert_at] + toc_block + without_toc[insert_at:]
    contents["word/document.xml"] = new_xml.encode("utf-8")

    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.writestr(name, contents[name])


__all__ = ["build_reference_docx", "move_toc_after_title"]
