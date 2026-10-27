from __future__ import annotations

from typing import List, Dict, Any

from app.models import DatabaseSchema, TableSchema, FieldSchema


def _normalize_db_schema(dbs: List[DatabaseSchema]) -> List[DatabaseSchema]:
    result = []
    for db in dbs:
        normalized_tables = []
        for table in db.tables:
            normalized_fields = [FieldSchema(name=f.name, type=f.type, description=f.description) for f in table.fields]
            normalized_tables.append(TableSchema(name=table.name, fields=normalized_fields))
        result.append(DatabaseSchema(name=db.name, dialect=db.dialect, tables=normalized_tables))
    return result


def _extract_index_terms(text: str) -> List[str]:
    cleaned = ''.join(ch.lower() if ch.isalnum() or ch.isspace() else ' ' for ch in text)
    terms = [term for term in cleaned.split() if len(term) > 2]
    return terms


def generate_source_mapping(dbs: List[DatabaseSchema]) -> Dict[str, Any]:
    normalized = _normalize_db_schema(dbs)
    global_field_index: Dict[str, List[str]] = {}
    for db in normalized:
        for table in db.tables:
            for field in table.fields:
                key = field.name.lower()
                global_field_index.setdefault(key, []).append(f"{db.name}.{table.name}.{field.name}")

    shared_fields = []
    seen = set()
    for field_name, occurrences in global_field_index.items():
        if len(occurrences) > 1:
            label = f"{field_name}"
            if label not in seen:
                seen.add(label)
                shared_fields.append({
                    "field": field_name,
                    "occurrences": occurrences,
                    "confidence": "medium" if len(occurrences) == 2 else "high",
                })

    conflicts = []
    for db in normalized:
        for table in db.tables:
            for field in table.fields:
                related = [
                    other
                    for other in shared_fields
                    if other["field"] == field.name.lower() and other["occurrences"]
                ]
                if related:
                    conflicts.append({
                        "database": db.name,
                        "table": table.name,
                        "field": field.name,
                        "issue": "field name overlaps across multiple sources",
                        "resolution": "standardize the field name or apply an explicit alias during join or comparison.",
                    })

    return {
        "shared_fields": shared_fields,
        "conflicts": conflicts,
        "mapping_summary": {
            "database_count": len(normalized),
            "shared_field_count": len(shared_fields),
            "potential_conflict_count": len(conflicts),
        },
    }


def generate_prompt(task: str, dbs: List[DatabaseSchema], mode: str = "single") -> str:
    if mode == "multi":
        return _generate_multi_db_prompt(task, dbs)
    return _generate_single_db_prompt(task, dbs)


def _generate_single_db_prompt(task: str, dbs: List[DatabaseSchema]) -> str:
    db = dbs[0] if dbs else DatabaseSchema(name="unknown", dialect="unknown")
    schema_summary = "\n".join(
        f"Table: {table.name}\nFields: {', '.join(f'{field.name} ({field.type})' for field in table.fields) or 'No fields available'}"
        for table in db.tables
    )
    return f"""
You are a scientific database research analyst.

Objective
----------
Your task is to investigate the following question:
{task}

Data Source
-----------
Database: {db.name}
Dialect: {db.dialect}

Relevant schema
---------------
{schema_summary}

Scientific Method
------------------
1. Define the research question precisely and identify the measurable outcome.
2. Confirm the relevant entities, keys, and time windows.
3. Determine the most direct join path and filtering logic.
4. Prefer field-level logic over broad scans.
5. Validate assumptions using sample checks before drawing conclusions.
6. Produce a concise evidence-based result with counts, qualifiers, and caveats.

Search Strategy
---------------
- Use the smallest necessary subset of tables and columns.
- Prefer explicit primary or foreign key relationships over fuzzy matching.
- Apply date, status, and segmentation filters before aggregation.
- When relevant, compute counts, rates, and distributions from the filtered dataset.
- If multiple interpretations exist, state assumptions clearly.

Constraints
-----------
- Do not invent data or fields.
- Do not assume data quality without checking nulls, duplicates, and missing values.
- Avoid broad joins unless necessary.
- For time-based work, use explicit date boundaries.
- Include evidence from the schema and query logic.

Output Requirements
-------------------
Return:
1. A short answer to the question.
2. The key tables and fields used.
3. The logical filtering and join strategy.
4. The final result, including counts or metrics when available.
5. Any assumptions, edge cases, or quality caveats.

Quality Control
---------------
- Verify the result against the schema.
- Check whether duplicates or nulls affect the conclusion.
- Compare the result with a sanity-check sample before finalizing.
"""


def _generate_multi_db_prompt(task: str, dbs: List[DatabaseSchema]) -> str:
    if not dbs:
        dbs = [DatabaseSchema(name="unknown", dialect="unknown")]

    db_summaries = []
    for db in dbs:
        summary = "\n".join(
            f"Table: {table.name}\nFields: {', '.join(f'{field.name} ({field.type})' for field in table.fields) or 'No fields available'}"
            for table in db.tables
        )
        db_summaries.append(f"Database: {db.name} ({db.dialect})\n{summary}")

    source_mapping = generate_source_mapping(dbs)
    shared_fields = ", ".join(item["field"] for item in source_mapping["shared_fields"][:5]) or "none identified"

    return f"""
You are a cross-database scientific research analyst.

Objective
----------
Investigate this research question across multiple data sources:
{task}

Available Data Sources
----------------------
{'\n\n'.join(db_summaries)}

Shared field mapping insights
----------------------------
Likely shared fields: {shared_fields}

Scientific Method
------------------
1. Clarify the exact entity being measured in each database.
2. Identify matching keys, fields, and semantics across systems.
3. Decide whether the task is an aggregation, comparison, or federated join problem.
4. Build a minimal, explainable evidence chain.
5. Validate consistency before comparing results across databases.

Cross-Database Strategy
----------------------
- Confirm whether each database represents the same business concept.
- Normalize naming differences before comparison.
- Prefer explicit key alignment and mapped dimensions.
- Use date and status filters consistently across all sources.
- Keep one source as the reference and identify divergences in others.
- When combining data, explain the mapping logic and assumptions.

Constraints
-----------
- Do not merge records without a defensible identifier or mapping rule.
- Do not compare incompatible metrics across databases.
- Document schema mismatches, null handling, and duplicates.
- Treat all source-specific assumptions as hypotheses requiring validation.

Output Requirements
-------------------
Return:
1. A clear cross-database summary.
2. The mapping between entities and fields.
3. The exact logic used to align records across systems.
4. The final result with counts, trends, or differences.
5. Caveats about data quality or semantic mismatch.
6. A recommended validation step.

Quality Control
---------------
- Confirm that all matching keys are truly comparable.
- Sanity-check sample records from each database.
- Check for duplicate entities and inconsistent field semantics.
- Highlight unresolved ambiguity explicitly.
"""
