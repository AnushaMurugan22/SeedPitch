
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings, get_settings
from app.usage import get_usage_summary, log_usage

app = FastAPI(title="SeedPitch", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]

PRIMARY_MODEL = "gemini-3.8-flash"


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    model: str
    status: str


def get_client(api_key: str):
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=300000),
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
def generate_answer(client, message: str, model: str):
    return client.models.generate_content(
        model=model,
        contents=message,
    )


@app.get("/")
def home():
    return {"message": "Welcome to SeedPitch API"}


@app.get("/health")
def health(settings: SettingsDep):
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/db-health")
def database_health(settings: SettingsDep):
    try:
        with psycopg.connect(
            settings.database_url,
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, settings: SettingsDep):
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is missing",
        )

    client = get_client(settings.gemini_api_key)

    try:
        response = generate_answer(
            client,
            request.message,
            PRIMARY_MODEL,
        )

        usage = response.usage_metadata

        input_tokens = (
            usage.prompt_token_count or 0 if usage else 0
        )
        output_tokens = (
            usage.candidates_token_count or 0 if usage else 0
        )

        log_usage(
            model=PRIMARY_MODEL,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_rate=settings.input_cost_per_million,
            output_rate=settings.output_cost_per_million,
        )

        return ChatResponse(
            answer=response.text or "No response generated",
            model=PRIMARY_MODEL,
            status="success",
        )

    except Exception as exc:
        print("GEMINI ERROR:", repr(exc))
        raise HTTPException(
            status_code=502,
            detail="Gemini API request failed",
        ) from exc


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

            # Use the same reliable generation method as /chat.
            # Then deliver the completed answer in text chunks.
            response = generate_answer(
                client,
                request.message,
                PRIMARY_MODEL,
            )

            answer = response.text or "No response generated"

            usage = response.usage_metadata

            input_tokens = (
                usage.prompt_token_count or 0 if usage else 0
            )
            output_tokens = (
                usage.candidates_token_count or 0 if usage else 0
            )

            log_usage(
                model=PRIMARY_MODEL,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_rate=settings.input_cost_per_million,
                output_rate=settings.output_cost_per_million,
            )

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


@app.get("/usage")
def usage():
    return get_usage_summary()
