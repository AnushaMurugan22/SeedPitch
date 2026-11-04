import math

from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embedding(client, text, task_type="RETRIEVAL_DOCUMENT"):
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=768,
        ),
    )

    values = response.embeddings[0].values

    magnitude = math.sqrt(sum(value * value for value in values))

    return [value / magnitude for value in values]
