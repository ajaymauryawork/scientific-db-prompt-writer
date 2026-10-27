from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.models import DatabaseSchema, FieldSchema, TableSchema


def _tokenize(value: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def _table_matches(task: str, table_name: str) -> bool:
    tokens = set(_tokenize(task))
    table_tokens = set(_tokenize(table_name))
    return bool(tokens & table_tokens) or table_name.lower() in task.lower()


def _field_matches(task: str, field_name: str) -> bool:
    task_tokens = set(_tokenize(task))
    field_tokens = set(_tokenize(field_name))
    return bool(task_tokens & field_tokens) or field_name.lower() in task.lower()


def _detect_aggregate(task: str) -> str:
    lower = task.lower()
    if any(word in lower for word in ["count", "number of", "how many"]):
        return "count"
    if any(word in lower for word in ["sum", "total", "revenue", "amount"]):
        return "sum"
    if "avg" in lower or "average" in lower:
        return "avg"
    return "select"


def _choose_tables(schema: DatabaseSchema, task: str) -> List[TableSchema]:
    matched = [table for table in schema.tables if _table_matches(task, table.name)]
    if matched:
        return matched
    return schema.tables[:2]


def _find_join_condition(tables: List[TableSchema]) -> Optional[Tuple[str, str, str]]:
    field_names = {field.name.lower() for table in tables for field in table.fields}
    for table_a in tables:
        for table_b in tables:
            if table_a.name == table_b.name:
                continue
            for field_a in table_a.fields:
                for field_b in table_b.fields:
                    if field_a.name.lower() == field_b.name.lower():
                        return table_a.name, field_a.name, table_b.name
    for table_a in tables:
        for table_b in tables:
            if table_a.name == table_b.name:
                continue
            for field_a in table_a.fields:
                for field_b in table_b.fields:
                    if "id" in field_a.name.lower() and "id" in field_b.name.lower() and field_a.name.lower().endswith(field_b.name.lower().replace("_id", "")):
                        return table_a.name, field_a.name, table_b.name
    return None


def generate_sql_from_prompt(task: str, schema: DatabaseSchema, dialect: str = "postgres") -> str:
    tables = _choose_tables(schema, task)
    if not tables:
        return "SELECT 1;"

    primary = tables[0]
    aggregate = _detect_aggregate(task)
    selected_fields = []
    for field in primary.fields:
        if _field_matches(task, field.name) or field.name.lower() in {"id", "name", "date", "amount", "total", "status"}:
            selected_fields.append(field.name)
    if not selected_fields:
        selected_fields = [field.name for field in primary.fields[:5]]

    select_clause = "*"
    if aggregate == "count":
        select_clause = "COUNT(*) AS total_records"
    elif aggregate == "sum":
        metric = next((field.name for field in primary.fields if "amount" in field.name.lower() or "total" in field.name.lower() or "value" in field.name.lower()), selected_fields[0])
        select_clause = f"SUM({metric}) AS total_value"
    elif aggregate == "avg":
        metric = next((field.name for field in primary.fields if "amount" in field.name.lower() or "total" in field.name.lower() or "value" in field.name.lower()), selected_fields[0])
        select_clause = f"AVG({metric}) AS avg_value"
    else:
        select_clause = ", ".join(selected_fields[:5])

    where_clauses: List[str] = []
    for field in primary.fields:
        if "date" in field.name.lower() and ("last" in task.lower() or "recent" in task.lower() or "month" in task.lower() or "week" in task.lower()):
            if dialect.lower() == "postgres":
                where_clauses.append(f"{field.name} >= CURRENT_DATE - INTERVAL '30 days'")
            elif dialect.lower() == "mysql":
                where_clauses.append(f"{field.name} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
            else:
                where_clauses.append(f"{field.name} >= date('now', '-30 days')")
            break
        if "status" in field.name.lower() and "active" in task.lower():
            where_clauses.append(f"{field.name} IN ('active', 'confirmed')")
            break

    if len(tables) > 1:
        join = _find_join_condition(tables)
        if join:
            left_table, left_field, right_table = join
            if left_table != primary.name:
                primary, right_table = right_table, primary.name
            join_sql = f" JOIN {right_table} ON {left_table}.{left_field} = {right_table}.{left_field}"
            if dialect.lower() == "mysql":
                if isinstance(primary, TableSchema):
                    pass
            if where_clauses:
                where_clause = " AND ".join(where_clauses)
            else:
                where_clause = "1 = 1"
            query = f"SELECT {select_clause} FROM {primary.name} {join_sql} WHERE {where_clause} LIMIT 100;"
            return query

    if where_clauses:
        where_clause = " AND ".join(where_clauses)
    else:
        where_clause = "1 = 1"

    if dialect.lower() == "mysql":
        return f"SELECT {select_clause} FROM `{primary.name}` WHERE {where_clause} LIMIT 100;"
    if dialect.lower() == "sqlite":
        return f"SELECT {select_clause} FROM \"{primary.name}\" WHERE {where_clause} LIMIT 100;"
    return f"SELECT {select_clause} FROM {primary.name} WHERE {where_clause} LIMIT 100;"


__all__ = ["generate_sql_from_prompt"]
