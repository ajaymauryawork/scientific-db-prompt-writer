from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.models import DatabaseSchema, FieldSchema, TableSchema


def _normalize(value: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def _table_score(table: TableSchema, task: str) -> int:
    tokens = set(_normalize(task))
    table_tokens = set(_normalize(table.name))
    score = len(tokens & table_tokens)
    for field in table.fields:
        if field.name.lower() in task.lower():
            score += 2
    return score


def _choose_tables(schema: DatabaseSchema, task: str) -> List[TableSchema]:
    ranked = sorted(schema.tables, key=lambda table: _table_score(table, task), reverse=True)
    if not ranked:
        return []
    return ranked[: min(3, len(ranked))]


def _pick_fields_for_table(table: TableSchema, task: str, limit: int = 5) -> List[str]:
    lower_task = task.lower()
    prioritized = []
    for field in table.fields:
        name = field.name.lower()
        if any(token in lower_task for token in [name, name.replace("_", " ")]):
            prioritized.append(field.name)
    if prioritized:
        return prioritized[:limit]
    for field in table.fields:
        if "id" in field.name.lower() or "date" in field.name.lower() or "amount" in field.name.lower() or "total" in field.name.lower() or "status" in field.name.lower() or "country" in field.name.lower():
            prioritized.append(field.name)
    if not prioritized:
        return [field.name for field in table.fields[:limit]]
    return prioritized[:limit]


def _detect_aggregate(task: str) -> str:
    lower = task.lower()
    if any(token in lower for token in ["count", "how many", "number of", "total records"]):
        return "count"
    if any(token in lower for token in ["sum", "total amount", "total revenue", "total spend", "grand total"]):
        return "sum"
    if any(token in lower for token in ["average", "avg", "mean"]):
        return "avg"
    return "select"


def _where_conditions_for_table(table: TableSchema, task: str, dialect: str) -> List[str]:
    low = task.lower()
    conditions: List[str] = []
    for field in table.fields:
        name = field.name.lower()
        if "date" in name or "time" in name:
            if any(word in low for word in ["last", "recent", "month", "week", "quarter", "year"]):
                if dialect.lower() == "postgres":
                    conditions.append(f"{table.name}.{field.name} >= CURRENT_DATE - INTERVAL '30 days'")
                elif dialect.lower() == "mysql":
                    conditions.append(f"{table.name}.{field.name} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
                else:
                    conditions.append(f"{table.name}.{field.name} >= date('now', '-30 days')")
                break
        if "status" in name and any(word in low for word in ["active", "confirmed", "open", "success", "complete"]):
            conditions.append(f"{table.name}.{field.name} IN ('active', 'confirmed')")
            break
    return conditions


def _find_join_keys(tables: List[TableSchema]) -> List[Tuple[str, str, str, str]]:
    field_map: Dict[str, List[Tuple[str, str]]] = {}
    for table in tables:
        for field in table.fields:
            field_map.setdefault(field.name.lower(), []).append((table.name, field.name))

    joins: List[Tuple[str, str, str, str]] = []
    for key, occurrences in field_map.items():
        if len(occurrences) >= 2 and (key.endswith("id") or key in {"customer_id", "user_id", "account_id", "order_id", "product_id"}):
            first = occurrences[0]
            second = occurrences[1]
            joins.append((first[0], first[1], second[0], second[1]))
    return joins


def _format_identifier(name: str, dialect: str) -> str:
    if dialect.lower() == "mysql":
        return f"`{name}`"
    if dialect.lower() == "sqlite":
        return f'"{name}"'
    return name


def generate_sql_from_prompt(task: str, schema: DatabaseSchema, dialect: str = "postgres") -> str:
    if not schema.tables:
        return "SELECT 1;"

    selected_tables = _choose_tables(schema, task)
    primary_table = selected_tables[0]
    aggregate = _detect_aggregate(task)

    metrics = []
    for field in primary_table.fields:
        lower = field.name.lower()
        if any(token in lower for token in ["amount", "total", "value", "price", "revenue", "cost", "sum"]):
            metrics.append(field.name)
    if not metrics:
        metrics = [field.name for field in primary_table.fields if field.name.lower() != "id"]

    selected_fields = _pick_fields_for_table(primary_table, task)
    if aggregate == "count":
        select_clause = "COUNT(*) AS total_records"
    elif aggregate == "sum":
        metric = next((field for field in metrics if field.lower() != "id"), selected_fields[0])
        select_clause = f"SUM({primary_table.name}.{metric}) AS total_value"
    elif aggregate == "avg":
        metric = next((field for field in metrics if field.lower() != "id"), selected_fields[0])
        select_clause = f"AVG({primary_table.name}.{metric}) AS avg_value"
    else:
        select_clause = ", ".join(f"{primary_table.name}.{field}" for field in selected_fields[:5])

    query_tables = [primary_table.name]
    join_sql = ""
    if len(selected_tables) > 1:
        joins = _find_join_keys(selected_tables)
        if joins:
            left_table, left_field, right_table, right_field = joins[0]
            if left_table not in query_tables:
                query_tables.append(left_table)
            if right_table not in query_tables:
                query_tables.append(right_table)
            join_sql = f" JOIN {right_table} ON {left_table}.{left_field} = {right_table}.{right_field}"
            if left_table == primary_table.name:
                select_clause = select_clause.replace(f"{primary_table.name}.", "") if f"{primary_table.name}." in select_clause else select_clause

    where_conditions: List[str] = []
    for table in selected_tables:
        where_conditions.extend(_where_conditions_for_table(table, task, dialect))

    final_where = " AND ".join(where_conditions) if where_conditions else "1 = 1"

    if dialect.lower() == "mysql":
        quote = lambda name: f"`{name}`"
        query = f"SELECT {select_clause} FROM {quote(primary_table.name)}"
        if join_sql:
            query += f" {join_sql.replace(primary_table.name, quote(primary_table.name)).replace(right_table, quote(right_table))}"
        query += f" WHERE {final_where} LIMIT 100;"
        return query

    if dialect.lower() == "sqlite":
        query = f"SELECT {select_clause} FROM \"{primary_table.name}\""
        if join_sql:
            extra = join_sql.replace(primary_table.name, f'"{primary_table.name}"').replace(right_table, f'"{right_table}"')
            query += f" {extra}"
        query += f" WHERE {final_where} LIMIT 100;"
        return query

    query = f"SELECT {select_clause} FROM {primary_table.name}"
    if join_sql:
        query += f" {join_sql}"
    query += f" WHERE {final_where} LIMIT 100;"
    return query


__all__ = ["generate_sql_from_prompt"]
