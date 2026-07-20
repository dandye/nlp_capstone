from pathlib import Path
from typing import Union
from pypdf import PdfReader


def extract_pdf_text(pdf_path: Union[Path, str]) -> str:
    """Extract text from PDF file."""
    try:
        pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path

        if not pdf_path.exists():
            return ""

        reader = PdfReader(pdf_path)
        text = ""

        for page in reader.pages:
            text += page.extract_text() + "\n"

        return text.strip()
    except Exception as e:
        print(f"Failed to extract text from {pdf_path}: {e}")
        return ""
