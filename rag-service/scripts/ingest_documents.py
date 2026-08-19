import os
import sys
import argparse

# Ensure app root is on pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ingestion_service import IngestionService


def ingest_data_directory(data_dir: str = "data"):
    if not os.path.exists(data_dir):
        print(f"Error: Directory '{data_dir}' not found.")
        sys.exit(1)

    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in '{data_dir}'.")
        return

    print("=" * 70)
    print(f" MEDICAL RAG INGESTION PIPELINE — {len(pdf_files)} PDF(s) found in {data_dir}")
    print("=" * 70)

    service = IngestionService()

    for idx, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(data_dir, filename)
        doc_id = os.path.splitext(filename)[0].replace(" ", "_").lower()
        title = filename.replace("_", " ").replace(".pdf", "").title()

        print(f"\n[{idx}/{len(pdf_files)}] Ingesting: {filename}")
        print(f"  Document ID: {doc_id}")
        print(f"  Title: {title}")

        try:
            result = service.ingest_pdf(
                document_path=file_path,
                document_id=doc_id,
                title=title,
            )
            print(f"  Status: {result.get('status')}")
            print(f"  Chunks Ingested: {result.get('chunks_ingested')}")
            print(f"  Message: {result.get('message')}")
        except Exception as e:
            print(f"  Error ingesting {filename}: {str(e)}")

    print("\n" + "=" * 70)
    print(" Ingestion complete.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDFs into Supabase Vector Store")
    parser.add_argument("--dir", type=str, default="data", help="Directory containing PDF files")
    args = parser.parse_args()

    ingest_data_directory(args.dir)
