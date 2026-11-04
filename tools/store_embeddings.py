
import json
import sys
import time
from pathlib import Path

import psycopg
from google import genai
from google.genai.errors import ClientError
from pgvector import Vector
from pgvector.psycopg import register_vector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.embeddings import generate_embedding


def main():
    settings = get_settings()

    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is missing in .env")

    client = genai.Client(api_key=settings.gemini_api_key)

    # Read all chunks
    with open("data/processed/chunks.jsonl", encoding="utf-8") as file:
        chunks = [json.loads(line) for line in file if line.strip()]

    print("Total chunks found:", len(chunks))

    stored = 0
    skipped = 0

    with psycopg.connect(settings.database_url) as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            for chunk in chunks:

                # Check whether chunk already exists
                cursor.execute(
                    """
                    SELECT id FROM document_chunks
                    WHERE document = %s
                    AND page_number = %s
                    AND chunk_number = %s
                    """,
                    (
                        chunk["document"],
                        chunk["page_number"],
                        chunk["chunk_number"],
                    ),
                )

                if cursor.fetchone():
                    skipped += 1
                    continue

                # Generate embedding
                try:
                    embedding = generate_embedding(
                        client,
                        chunk["text"],
                    )

                except ClientError as e:
                    if e.code == 429:
                        print("\nGemini daily quota exceeded!")
                        print("Successfully stored:", stored)
                        print("Existing chunks skipped:", skipped)
                        print("Wait for quota reset and run this script again.")
                        return

                    raise

                # Store chunk and embedding
                cursor.execute(
                    """
                    INSERT INTO document_chunks
                    (document, page_number, chunk_number,
                     headings, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        chunk["document"],
                        chunk["page_number"],
                        chunk["chunk_number"],
                        json.dumps(chunk["headings"]),
                        chunk["text"],
                        Vector(embedding),
                    ),
                )

                # Save every successful insertion
                connection.commit()

                stored += 1

                print(
                    f"Stored: {stored} | "
                    f"{chunk['document']} | Page {chunk['page_number']}"
                )

                time.sleep(1.5)

    print("\nEmbedding process completed!")
    print("New chunks stored:", stored)
    print("Existing chunks skipped:", skipped)


if __name__ == "__main__":
    main()
