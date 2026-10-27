import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from app.db.discovery import discover_database_metadata
from app.models import DatabaseSchema, PromptRequest, SchemaDiscoveryRequest, SQLGenerationRequest
from app.prompting.prompt_writer import generate_prompt, generate_source_mapping
from app.sql.generator import generate_sql_from_prompt

app = FastAPI(title="Scientific Database Prompt Writer", version="1.0.0")


class Settings(BaseModel):
    database_url: Optional[str] = os.getenv("DATABASE_URL")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/schema/discover")
def discover_schema(payload: SchemaDiscoveryRequest) -> Dict[str, Any]:
    db_url = payload.database_url or Settings().database_url
    if not db_url:
        raise ValueError("database_url is required. Set DATABASE_URL or send it in the request body.")
    schema = discover_database_metadata(db_url, payload.dialect)
    return {"database": schema.model_dump()}


@app.post("/api/prompts/generate")
def generate_prompt_endpoint(payload: PromptRequest) -> Dict[str, Any]:
    prompt = generate_prompt(payload.task, payload.databases, payload.mode)
    mapping = generate_source_mapping(payload.databases) if payload.mode == "multi" else None
    return {"prompt": prompt, "mode": payload.mode, "source_mapping": mapping}


@app.post("/api/sql/generate")
def generate_sql_endpoint(payload: SQLGenerationRequest) -> Dict[str, str]:
    sql = generate_sql_from_prompt(payload.task, payload.schema, payload.dialect)
    return {"sql": sql}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
