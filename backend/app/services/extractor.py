import os
import ebooklib  #
import mobi
import fitz
import tempfile
import shutil
from ebooklib import epub
from docx import Document
from html.parser import HTMLParser

class _StripHTML(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)

def extract_text(file_path: str) -> str:

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext == ".epub":
        return _extract_epub(file_path)
    elif ext == ".mobi":
        return _extract_mobi(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    return "\n".join(page.get_text() for page in doc)

def _extract_mobi(file_path: str) -> str:

    tempdir, book = mobi.extract(file_path)
    with open(book, "r", encoding="utf-8") as f:
        text = f.read()
    parser = _StripHTML()
    parser.feed(text)
    shutil.rmtree(tempdir)

    return "".join(parser.parts)


def _extract_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_epub(file_path: str) -> str:

    book = epub.read_epub(file_path)
    chunks = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        parser = _StripHTML()
        parser.feed(item.get_content().decode("utf-8", errors="ignore"))
        chunks.append("".join(parser.parts))
    return "\n".join(chunks).strip()
