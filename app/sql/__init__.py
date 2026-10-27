import re


def _normalize_name(value: str) -> str:
    return re.sub(r'[^a-z0-9_]+', '_', value.lower()).strip('_')


def _table_candidates(schema: dict, task: str) -> list[str]:
    task_tokens = set(_normalize_name(token) for token in task.lower().split())
    matches = []
    for table in schema.get("tables", []):
        t_name = _normalize_name(table.get("name", ""))
        table_tokens = set(_normalize_name(token) for token in t_name.split('_'))
        if task_tokens.intersection(table_tokens):
            matches.append(table.get("name"))
    if matches:
        return matches
    return [table.get("name") for table in schema.get("tables", [])[:1] if table.get("name")]


def _field_candidates(table: dict, task: str) -> list[str]:
    task_lower = task.lower()
    fields = []
    for field in table.get("fields", []):
        name = field.get("name", "")
        if any(keyword in task_lower for keyword in [name.lower(), name.lower().replace('_', ' ')]):
            fields.append(name)
    return fields or [f.get("name") for f in table.get("fields", [])[:3] if f.get("name")]


def _build_where_clause(task: str, table: dict) -> str:
    lower = task.lower()
    filters = []
    field_names = [f.get("name", "") for f in table.get("fields", [])]
    for field in field_names:
        lname = field.lower()
        if "date" in lname or "time" in lname:
            filters.append(f"{field} >= CURRENT_DATE - INTERVAL '30 days'")
            break
        if "status" in lname:
            filters.append(f"{field} IN ('active', 'confirmed')")
            break
    if not filters:
        filters.append("1 = 1")
    return " AND ".join(filters)


def generate_sql_from_prompt(task: str, schema: dict, dialect: str = "postgres") -> str:
    tables = schema.get("tables", [])
    if not tables:
        return "SELECT 1;"

    primary_table = _table_candidates(schema, task)[0]
    table_obj = next((table for table in tables if table.get("name") == primary_table), tables[0])

    fields = _field_candidates(table_obj, task)
    select_columns = ", ".join(fields[:5]) if fields else "*"
    where_clause = _build_where_clause(task, table_obj)

    if dialect.lower() == "mysql":
        return f"SELECT {select_columns} FROM {primary_table} WHERE {where_clause} LIMIT 100;"
    if dialect.lower() == "sqlite":
        return f"SELECT {select_columns} FROM \"{primary_table}\" WHERE {where_clause} LIMIT 100;"
    return f"SELECT {select_columns} FROM {primary_table} WHERE {where_clause} LIMIT 100;"
