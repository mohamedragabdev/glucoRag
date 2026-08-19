import os
from typing import List
from langchain_core.documents import Document
from pypdf import PdfReader


def load_pdf_document(file_path: str, document_id: str, title: str) -> List[Document]:
    """
    Loads a PDF document page-by-page.
    Only uses loader-provided metadata (source and 1-indexed page number).
    Never fabricates metadata fields.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF document not found at: {file_path}")

    reader = PdfReader(file_path)
    documents = []

    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            doc = Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(file_path),
                    "page_number": page_idx + 1,  # 1-indexed for human display
                    "document_id": document_id,
                    "title": title,
                },
            )
            documents.append(doc)

    return documents
