from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from sqlalchemy import inspect
from sqlalchemy.engine import Engine


@dataclass
class FieldDefinition:
    name: str
    type: str = "unknown"
    description: str = ""


@dataclass
class TableDefinition:
    name: str
    fields: List[FieldDefinition] = field(default_factory=list)


@dataclass
class DatabaseDefinition:
    name: str
    dialect: str = "unknown"
    tables: List[TableDefinition] = field(default_factory=list)


def guess_dialect(database_url: str, dialect: str | None = None) -> str:
    if dialect:
        return dialect.lower()
    url = database_url.lower()
    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith("postgresql") or url.startswith("postgres"):
        return "postgres"
    if url.startswith("mysql"):
        return "mysql"
    return "unknown"


def _normalize_sqlalchemy_columns(columns: list[dict]) -> List[FieldDefinition]:
    fields: List[FieldDefinition] = []
    for column in columns:
        name = str(column.get("name") or column.get("column_name") or "unknown")
        field_type = str(column.get("type") or column.get("data_type") or "unknown")
        fields.append(FieldDefinition(name=name, type=str(field_type)))
    return fields


def discover_database_metadata(database_url: str, dialect: str | None = None) -> DatabaseDefinition:
    detected_dialect = guess_dialect(database_url, dialect)
    if detected_dialect == "sqlite":
        return _discover_sqlite(database_url)
    if detected_dialect == "postgres":
        return _discover_postgres(database_url)
    if detected_dialect == "mysql":
        return _discover_mysql(database_url)
    raise ValueError(f"Unsupported database dialect: {detected_dialect}")


def _discover_sqlite(database_url: str) -> DatabaseDefinition:
    import sqlite3

    db_path = database_url.replace("sqlite:///", "").replace("sqlite://", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    ).fetchall()

    schema = DatabaseDefinition(name="sqlite_db", dialect="sqlite")
    for (table_name,) in tables:
        columns = cursor.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        fields = [FieldDefinition(name=str(col[1]), type=str(col[2] or "unknown")) for col in columns]
        schema.tables.append(TableDefinition(name=table_name, fields=fields))
    conn.close()
    return schema


def _discover_postgres(database_url: str) -> DatabaseDefinition:
    from sqlalchemy import create_engine

    engine = create_engine(database_url)
    inspector = inspect(engine)
    names = inspector.get_table_names()
    db_name = engine.url.database or "postgres_db"
    schema = DatabaseDefinition(name=db_name, dialect="postgres")
    for table_name in names:
        columns = inspector.get_columns(table_name)
        fields = _normalize_sqlalchemy_columns(columns)
        schema.tables.append(TableDefinition(name=table_name, fields=fields))
    engine.dispose()
    return schema


def _discover_mysql(database_url: str) -> DatabaseDefinition:
    from sqlalchemy import create_engine

    engine = create_engine(database_url)
    inspector = inspect(engine)
    names = inspector.get_table_names()
    db_name = engine.url.database or "mysql_db"
    schema = DatabaseDefinition(name=db_name, dialect="mysql")
    for table_name in names:
        columns = inspector.get_columns(table_name)
        fields = _normalize_sqlalchemy_columns(columns)
        schema.tables.append(TableDefinition(name=table_name, fields=fields))
    engine.dispose()
    return schema
