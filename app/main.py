
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings, get_settings
from app.embeddings import generate_embedding
from app.retriever import search_documents
from app.usage import get_usage_summary, log_usage

app = FastAPI(title="SeedPitch", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"


# Request and response models

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    model: str
    status: str


class AskRequest(BaseModel):
    question: str


# Gemini client

def get_client(api_key: str):
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=300000),
    )


# Retry primary model up to 3 times

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
def generate_primary(client, message: str):
    return client.models.generate_content(
        model=PRIMARY_MODEL,
        contents=message,
    )


# Primary model with fallback

def generate_answer(client, message: str):
    try:
        response = generate_primary(client, message)
        return response, PRIMARY_MODEL

    except Exception as primary_error:
        print("PRIMARY MODEL FAILED:", repr(primary_error))

        try:
            response = client.models.generate_content(
                model=FALLBACK_MODEL,
                contents=message,
            )
            return response, FALLBACK_MODEL

        except Exception as fallback_error:
            print("FALLBACK MODEL FAILED:", repr(fallback_error))
            raise fallback_error


# Save token usage

def save_usage(response, model, settings):
    usage = response.usage_metadata

    input_tokens = (
        usage.prompt_token_count or 0 if usage else 0
    )

    output_tokens = (
        usage.candidates_token_count or 0 if usage else 0
    )

    log_usage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_rate=settings.input_cost_per_million,
        output_rate=settings.output_cost_per_million,
    )


# Home endpoint

@app.get("/")
def home():
    return {"message": "Welcome to SeedPitch API"}


# Health endpoint

@app.get("/health")
def health(settings: SettingsDep):
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


# Database health endpoint

@app.get("/db-health")
def database_health(settings: SettingsDep):
    try:
        with psycopg.connect(
            settings.database_url,
            connect_timeout=5,
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT extversion FROM pg_extension "
                    "WHERE extname = 'vector'"
                )
                result = cursor.fetchone()

        if result is None:
            raise HTTPException(
                status_code=503,
                detail="pgvector extension is not enabled",
            )

        return {
            "database": "connected",
            "pgvector": "enabled",
            "pgvector_version": result[0],
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("DATABASE ERROR:", repr(exc))

        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc


# Normal chat endpoint

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, settings: SettingsDep):

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is missing",
        )

    try:
        client = get_client(settings.gemini_api_key)

        response, used_model = generate_answer(
            client,
            request.message,
        )

        save_usage(response, used_model, settings)

        return ChatResponse(
            answer=response.text or "No response generated",
            model=used_model,
            status="success",
        )

    except Exception as exc:
        print("GEMINI ERROR:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail="Both Gemini models failed",
        ) from exc


# Streaming endpoint

@app.post("/chat/stream")
def chat_stream(request: ChatRequest, settings: SettingsDep):

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is missing",
        )

    def generate():
        try:
            client = get_client(settings.gemini_api_key)

            response, used_model = generate_answer(
                client,
                request.message,
            )

            save_usage(response, used_model, settings)

            answer = response.text or "No response generated"

            words = answer.split(" ")

            for word in words:
                yield word + " "

        except Exception as exc:
            print("STREAM ERROR:", repr(exc))
            yield "\n[Generation failed]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )


# Usage endpoint

@app.get("/usage")
def usage():
    return get_usage_summary()


# Document question-answering endpoint

@app.post("/ask")
def ask(request: AskRequest, settings: SettingsDep):

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is missing",
        )

    try:
        client = get_client(settings.gemini_api_key)

        # Generate embedding for the user's question
        query_embedding = generate_embedding(
            client,
            request.question,
            task_type="RETRIEVAL_QUERY",
        )

        # Retrieve the five most relevant document chunks
        results = search_documents(
            settings.database_url,
            query_embedding,
            limit=8,
        )

        if not results:
            return {
                "answer": "No relevant documents found.",
                "citations": [],
                "status": "no_results",
            }

        # Build context from retrieved chunks
        context = ""

        for item in results:
            context += (
                f"\nDocument: {item['document']}\n"
                f"Page: {item['page_number']}\n"
                f"Content: {item['content']}\n"
            )

        prompt = f"""
        Answer the question using ONLY the context below.

        If the answer is not available in the context,
        clearly say that the information was not found.

        Include document name and page number citations
        wherever relevant.

        Context:
        {context}

        Question:
        {request.question}
        """

        response, used_model = generate_answer(
            client,
            prompt,
        )

        save_usage(response, used_model, settings)

        # Prepare citations
        citations = [
            {
                "document": item["document"],
                "page": item["page_number"],
            }
            for item in results
        ]

        return {
            "answer": response.text or "No answer generated",
            "citations": citations,
            "model": used_model,
            "status": "success",
        }

    except Exception as exc:
        print("ASK ERROR:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail="Question answering failed",
        ) from exc
