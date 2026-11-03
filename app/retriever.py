import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector


def search_documents(database_url, query_embedding, limit=8):

    results = []

    with psycopg.connect(database_url) as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT document, page_number, chunk_number,
                       headings, content
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (Vector(query_embedding), limit),
            )

            rows = cursor.fetchall()

            for row in rows:
                results.append({
                    "document": row[0],
                    "page_number": row[1],
                    "chunk_number": row[2],
                    "headings": row[3],
                    "content": row[4],
                })

    return results
