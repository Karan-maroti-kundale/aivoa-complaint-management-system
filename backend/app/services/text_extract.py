from email import policy
from email.parser import BytesParser
from io import BytesIO
from docx import Document
from pypdf import PdfReader

MAX_FILE_BYTES = 10 * 1024 * 1024


def extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def extract_docx_text(data: bytes) -> str:
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def extract_eml_text(data: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(data)
    parts = []
    subject = msg.get("subject")
    if subject:
        parts.append(f"Subject: {subject}")
    from_ = msg.get("from")
    if from_:
        parts.append(f"From: {from_}")
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                parts.append(part.get_content())
    elif msg.get_content_type() == "text/plain":
        parts.append(msg.get_content())
    return "\n\n".join(p.strip() for p in parts if p and p.strip()).strip()


def extract_document_text(filename: str, data: bytes) -> str:
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("File exceeds the 10 MB upload limit.")
    suffix = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if suffix == 'pdf':
        return extract_pdf_text(data)
    if suffix == 'docx':
        return extract_docx_text(data)
    if suffix == 'eml':
        return extract_eml_text(data)
    if suffix == 'txt':
        return data.decode('utf-8', errors='ignore').strip()
    raise ValueError("Unsupported file type. Use PDF, DOCX, TXT, or EML.")
