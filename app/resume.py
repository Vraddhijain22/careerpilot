import re
import fitz

MAX_RESUME_CHARS = 30000


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a user-uploaded PDF in memory; does not save the PDF."""
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("The uploaded file does not appear to be a valid PDF.")
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "\n".join(page.get_text("text") for page in doc)
    except Exception as exc:
        raise ValueError("Could not read this PDF. Try exporting it as a text-searchable PDF.") from exc
    text = clean_resume(text)
    if not text.strip():
        raise ValueError("No selectable text found. This may be a scanned PDF; paste the resume text instead.")
    return text


def clean_resume(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:MAX_RESUME_CHARS]
