import os
import argparse
import fitz  # PyMuPDF
import hashlib

from whoosh import index
from whoosh.fields import Schema, ID, NUMERIC, TEXT, STORED

APP_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(APP_DIR, "storage", "index")

def get_index(create=True):
    schema = Schema(
        doc_id=ID(stored=True, unique=True),
        filename=STORED,   # only the filename (not full path)
        title=TEXT(stored=True),
        page=NUMERIC(stored=True),
        content=TEXT
    )
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR, exist_ok=True)
    if create and not index.exists_in(INDEX_DIR):
        return index.create_in(INDEX_DIR, schema)
    return index.open_dir(INDEX_DIR)

def file_page_id(path: str, page: int) -> str:
    h = hashlib.sha1()
    h.update(path.encode("utf-8", errors="ignore"))
    h.update(b"::")
    h.update(str(page).encode("utf-8"))
    return h.hexdigest()

def extract_pages(pdf_path: str):
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            try:
                text = page.get_text("text") or ""
            except Exception:
                text = ""
            yield i, text

def walk_pdfs(folder):
    for root, dirs, files in os.walk(folder):
        for name in files:
            if name.lower().endswith(".pdf"):
                yield os.path.join(root, name)

def main():
    parser = argparse.ArgumentParser(description="Bulk index PDFs into Whoosh (page-level)")
    parser.add_argument("--folder", required=True, help="Folder containing PDFs")
    args = parser.parse_args()

    ix = get_index(create=True)
    writer = ix.writer(limitmb=256, procs=0, multisegment=True)
    try:
        for pdf_path in walk_pdfs(args.folder):
            # ✅ only keep filename, not folder path
            filename = os.path.basename(pdf_path)
            print(f"Indexing: {filename}")
            for page_num, text in extract_pages(pdf_path):
                docid = file_page_id(filename, page_num)
                writer.update_document(
                    doc_id=docid,
                    filename=filename,   # ✅ only filename
                    title=filename,
                    page=page_num,
                    content=text
                )
        print("Committing index ...")
    finally:
        writer.commit()
    print("Done.")

if __name__ == "__main__":
    main()
