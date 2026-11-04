import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parser import parse_pdf

RAW_FOLDER = Path("data/raw")
OUTPUT_FILE = Path("data/processed/pages.jsonl")


def get_file_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(4096), b""):
            sha256.update(block)

    return sha256.hexdigest()


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    pdf_files = list(RAW_FOLDER.glob("*.pdf"))

    seen_files = set()
    total_pages = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        for pdf_path in pdf_files:
            file_hash = get_file_hash(pdf_path)

            if file_hash in seen_files:
                print("Skipping duplicate:", pdf_path.name)
                continue

            seen_files.add(file_hash)

            print("Processing:", pdf_path.name)

            pages = parse_pdf(str(pdf_path))

            for page in pages:
                record = {
                    "document": pdf_path.name,
                    "page_number": page["page_number"],
                    "headings": page["headings"],
                    "text": page["text"],
                }

                output.write(json.dumps(record, ensure_ascii=False) + "\n")

                total_pages += 1

    print("\nParsing completed!")
    print("Total pages processed:", total_pages)
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
