# Scientific Database Prompt Writer

A production-ready Python project that generates scientific database prompts, discovers DB metadata, generates SQL, and exposes a REST API for single- and multi-database workflows.

## Features

- Scientific prompt writer for one or many databases
- Metadata auto-discovery for PostgreSQL, MySQL, and SQLite
- SQL generation from research questions and schema context
- Multi-database source mapping and conflict resolution
- FastAPI web API
- Test coverage for prompt and SQL generation

## Repository layout

```text
scientific-db-prompt-writer/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── discovery.py
│   ├── prompting/
│   │   ├── __init__.py
│   │   └── prompt_writer.py
│   └── sql/
│       ├── __init__.py
│       └── generator.py
├── tests/
│   ├── __init__.py
│   ├── test_prompt_writer.py
│   └── test_sql_generator.py
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── sample_db_config.json
```

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Explore the API

Open:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Example: generate a prompt

```bash
curl -X POST "http://localhost:8000/api/prompts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Find high-value customers in Europe who purchased more than twice in the last quarter.",
    "mode": "single",
    "databases": [{
      "name": "sales_db",
      "dialect": "postgres",
      "tables": [
        {"name": "customers", "fields": [
          {"name": "customer_id", "type": "integer"},
          {"name": "country", "type": "text"},
          {"name": "signup_date", "type": "date"}
        ]},
        {"name": "orders", "fields": [
          {"name": "order_id", "type": "integer"},
          {"name": "customer_id", "type": "integer"},
          {"name": "order_date", "type": "date"},
          {"name": "amount", "type": "numeric"}
        ]}
      ]
    }]
  }'
```

## Example: generate SQL from a prompt

```bash
curl -X POST "http://localhost:8000/api/sql/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Show customers with more than three orders and a total spend above $5000.",
    "dialect": "postgres",
    "schema": {
      "name": "sales_db",
      "dialect": "postgres",
      "tables": [{
        "name": "customers",
        "fields": [{"name": "customer_id", "type": "integer"}, {"name": "country", "type": "text"}]
      }, {
        "name": "orders",
        "fields": [{"name": "order_id", "type": "integer"}, {"name": "customer_id", "type": "integer"}, {"name": "amount", "type": "numeric"}]
      }]
    }
  }'
```

## Example: discover metadata from a real database

```bash
curl -X POST "http://localhost:8000/api/schema/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales_db",
    "database_url": "postgresql://user:pass@localhost:5432/sales_db",
    "dialect": "postgres"
  }'
```

## Multi-database source mapping

For multi-database mode, the project computes:

- shared entities across databases
- field overlap mappings
- likely join/merge candidates
- conflict resolution suggestions

This helps produce prompts that compare and align data from multiple systems instead of blindly merging sources.

## Scientific prompt structure

The generated prompt includes:

- objective
- relevant schema
- scientific method
- search strategy
- constraints
- output requirements
- validation and quality control guidance

## Testing

```bash
pytest -q
```

## Notes

This project is intentionally designed to be useful for data research, analytics QA, and AI-assisted database exploration. It combines schema awareness with scientific reasoning to create more robust prompts and safer SQL generation.
