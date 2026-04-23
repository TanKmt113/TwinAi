import csv
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


class DocumentParseError(RuntimeError):
    pass


def parse_document(content: bytes, file_name: str, file_type: str | None = None) -> str:
    extension = (file_type or Path(file_name).suffix.lstrip(".")).lower()
    if extension in {"txt", "md"}:
        return _decode_text_bytes(content)
    if extension == "csv":
        return _parse_csv(content)
    if extension == "pdf":
        return _parse_pdf(content)
    if extension == "docx":
        return _parse_docx(content)
    if extension == "doc":
        raise DocumentParseError("Legacy .doc files are not supported yet. Please upload .docx, .pdf or text files.")
    return _decode_text_bytes(content)


def _decode_text_bytes(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            text = content.decode(encoding)
            if _looks_like_text(text):
                return text.strip()
        except UnicodeDecodeError:
            continue
    raise DocumentParseError("Unable to decode text content from uploaded file.")


def _parse_csv(content: bytes) -> str:
    text = _decode_text_bytes(content)
    reader = csv.reader(StringIO(text))
    rows = [" | ".join(cell.strip() for cell in row if cell.strip()) for row in reader]
    return "\n".join(row for row in rows if row).strip()


def _parse_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:  # pragma: no cover - environment-specific
        raise DocumentParseError("pypdf is required to parse PDF manuals. Rebuild backend dependencies first.") from exc
    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise DocumentParseError(f"Unable to parse PDF: {exc}") from exc

    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(page for page in pages if page)
    if not text:
        raise DocumentParseError("PDF does not contain extractable text.")
    return text


def _parse_docx(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            xml_bytes = archive.read("word/document.xml")
    except Exception as exc:
        raise DocumentParseError(f"Unable to parse DOCX: {exc}") from exc

    root = ElementTree.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    if not paragraphs:
        raise DocumentParseError("DOCX does not contain extractable text.")
    return "\n\n".join(paragraphs)


def _looks_like_text(text: str) -> bool:
    if not text.strip():
        return False
    printable_count = sum(1 for char in text if char.isprintable() or char in "\n\r\t")
    return printable_count / max(len(text), 1) >= 0.9
