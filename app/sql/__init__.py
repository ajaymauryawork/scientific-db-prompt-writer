from __future__ import annotations

from typing import List

from app.models import DatabaseSchema, TableSchema


def _table_candidates(schema: DatabaseSchema, task: str) -> List[str]:
    task_tokens = {token.lower() for token in task.replace("_", " ").split() if len(token) > 2}
    matches: List[str] = []
    for table in schema.tables:
        table_tokens = {token.lower() for token in table.name.replace("_", " ").split() if len(token) > 2}
        if task_tokens.intersection(table_tokens):
            matches.append(table.name)
    if matches:
        return matches
    return [table.name for table in schema.tables[:1]]


def _field_candidates(table: TableSchema, task: str) -> List[str]:
    task_lower = task.lower()
    hits: List[str] = []
    for field in table.fields:
        lowered = field.name.lower()
        if any(token in task_lower for token in [lowered, lowered.replace("_", " ")]):
            hits.append(field.name)
    if hits:
        return hits
    return [field.name for field in table.fields[:3]]


def _where_clause(table: TableSchema, task: str, dialect: str) -> str:
    filter_candidates = []
    for field in table.fields:
        lname = field.name.lower()
        if "date" in lname or "time" in lname:
            if dialect.lower() == "postgres":
                filter_candidates.append(f"{field.name} >= CURRENT_DATE - INTERVAL '30 days'")
            elif dialect.lower() == "mysql":
                filter_candidates.append(f"{field.name} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
            else:
                filter_candidates.append(f"{field.name} >= date('now', '-30 days')")
            break
        if "status" in lname:
            filter_candidates.append(f"{field.name} IN ('active', 'confirmed')")
            break
    return " AND ".join(filter_candidates) if filter_candidates else "1 = 1"


def generate_sql_from_prompt(task: str, schema: DatabaseSchema, dialect: str = "postgres") -> str:
    if not schema.tables:
        return "SELECT 1;"

    table_name = _table_candidates(schema, task)[0]
    table = next((entry for entry in schema.tables if entry.name == table_name), schema.tables[0])
    fields = _field_candidates(table, task)
    select_columns = ", ".join(fields[:5]) if fields else "*"
    where_clause = _where_clause(table, task, dialect)

    if dialect.lower() == "mysql":
        return f"SELECT {select_columns} FROM `{table_name}` WHERE {where_clause} LIMIT 100;"
    if dialect.lower() == "sqlite":
        return f"SELECT {select_columns} FROM \"{table_name}\" WHERE {where_clause} LIMIT 100;"
    return f"SELECT {select_columns} FROM {table_name} WHERE {where_clause} LIMIT 100;"


__all__ = ["generate_sql_from_prompt"]
