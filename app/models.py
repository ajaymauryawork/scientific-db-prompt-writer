from typing import List, Optional

from pydantic import BaseModel, Field


class FieldSchema(BaseModel):
    name: str
    type: str = "unknown"
    description: Optional[str] = None


class TableSchema(BaseModel):
    name: str
    fields: List[FieldSchema] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    name: str
    dialect: str = "unknown"
    tables: List[TableSchema] = Field(default_factory=list)


class SchemaDiscoveryRequest(BaseModel):
    name: str = "database"
    database_url: str
    dialect: Optional[str] = None


class PromptRequest(BaseModel):
    task: str
    mode: str = "single"
    databases: List[DatabaseSchema] = Field(default_factory=list)


class SQLGenerationRequest(BaseModel):
    task: str
    dialect: str = "postgres"
    schema: DatabaseSchema


class PromptResponse(BaseModel):
    prompt: str
    mode: str
    source_mapping: Optional[dict] = None
