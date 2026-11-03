import json
from pathlib import Path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunker import create_chunks

INPUT_FILE = Path("data/processed/pages.jsonl")
OUTPUT_FILE = Path("data/processed/chunks.jsonl")


def main():
    total_chunks = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as source:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as output:

            for line in source:
                page = json.loads(line)

                chunks = create_chunks(page["text"])

                for index, chunk in enumerate(chunks, start=1):
                    record = {
                        "document": page["document"],
                        "page_number": page["page_number"],
                        "headings": page["headings"],
                        "chunk_number": index,
                        "text": chunk
                    }

                    output.write(
                        json.dumps(record, ensure_ascii=False) + "\n"
                    )

                    total_chunks += 1

    print("Chunking completed!")
    print("Total chunks:", total_chunks)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
