from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings


def chunk_documents(documents: List[Document], document_id: str, title: str) -> List[Document]:
    """
    Chunks documents using RecursiveCharacterTextSplitter with configurable size and overlap.
    Assigns deterministic chunk IDs: {document_id}_p{page}_c{chunk_index}
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )

    chunked_docs = []

    for doc in documents:
        page_num = doc.metadata.get("page_number", 1)
        sub_docs = text_splitter.split_text(doc.page_content)

        for chunk_idx, chunk_text in enumerate(sub_docs):
            chunk_id = f"{document_id}_p{page_num}_c{chunk_idx + 1}"
            chunked_doc = Document(
                page_content=chunk_text,
                metadata={
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "title": title,
                    "page_number": page_num,
                    "chunk_index": chunk_idx + 1,
                },
            )
            chunked_docs.append(chunked_doc)

    return chunked_docs
