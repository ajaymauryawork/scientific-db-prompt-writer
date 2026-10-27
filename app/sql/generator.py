from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from sqlalchemy import create_engine, inspect

from app.models import DatabaseSchema, FieldSchema, TableSchema


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


def _normalize_sqlalchemy_columns(columns: List[Dict[str, Any]]) -> List[FieldSchema]:
    result: List[FieldSchema] = []
    for column in columns:
        name = str(column.get("name") or column.get("column_name") or "unknown")
        field_type = str(column.get("type") or column.get("data_type") or "unknown")
        result.append(FieldSchema(name=name, type=str(field_type)))
    return result


def _discover_sqlite(database_url: str) -> DatabaseSchema:
    db_path = database_url.replace("sqlite:///", "").replace("sqlite://", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    ).fetchall()

    schema = DatabaseSchema(name="sqlite_db", dialect="sqlite")
    for (table_name,) in tables:
        columns = cursor.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        fields = [FieldSchema(name=str(col[1]), type=str(col[2] or "unknown")) for col in columns]
        schema.tables.append(TableSchema(name=table_name, fields=fields))
    conn.close()
    return schema


def _discover_postgres(database_url: str) -> DatabaseSchema:
    engine = create_engine(database_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    db_name = engine.url.database or "postgres_db"
    schema = DatabaseSchema(name=db_name, dialect="postgres")
    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        schema.tables.append(TableSchema(name=table_name, fields=_normalize_sqlalchemy_columns(columns)))
    engine.dispose()
    return schema


def _discover_mysql(database_url: str) -> DatabaseSchema:
    engine = create_engine(database_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    db_name = engine.url.database or "mysql_db"
    schema = DatabaseSchema(name=db_name, dialect="mysql")
    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        schema.tables.append(TableSchema(name=table_name, fields=_normalize_sqlalchemy_columns(columns)))
    engine.dispose()
    return schema


def discover_database_metadata(database_url: str, dialect: str | None = None) -> DatabaseSchema:
    detected_dialect = guess_dialect(database_url, dialect)
    if detected_dialect == "sqlite":
        return _discover_sqlite(database_url)
    if detected_dialect == "postgres":
        return _discover_postgres(database_url)
    if detected_dialect == "mysql":
        return _discover_mysql(database_url)
    raise ValueError(f"Unsupported database dialect: {detected_dialect}")


__all__ = [
    "guess_dialect",
    "discover_database_metadata",
]
