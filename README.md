# Scientific Database Prompt Writer

A production-ready Python project that generates scientific database prompts, discovers database metadata, generates SQL, and exposes a REST API for single- and multi-database workflows.

## Support and Contributions

If you would like to support this project, you can contribute via the UPI QR code below.

Save the QR image file as `docs/upi-qr.png` and then use the following snippet in this README:

```md
![UPI QR for AJAY MAURYA](docs/upi-qr.png)

UPI ID: `8114286022@upi`
Name: `AJAY MAURYA`
```

This allows users who want to contribute small amounts to easily scan the QR code and support the project.

## Features

- Scientific prompt writer for one or many databases
- Metadata auto-discovery for PostgreSQL, MySQL, and SQLite
- SQL generation from research questions and schema context
- Multi-database source mapping and conflict resolution
- FastAPI web API
- Docker deployment support
- Environment-based configuration
- PostgreSQL seed schema for quick local testing

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
├── scripts/
│   └── seed_postgres.sql
├── tests/
│   ├── test_prompt_writer.py
│   └── test_sql_generator.py
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── docker-compose.yml
├── requirements.txt
├── run.py
├── sample_db_config.json
└── .dockerignore
```

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Example `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/appdb
APP_PORT=8000
```

### 3. Start PostgreSQL locally

Using Docker Compose:

```bash
docker-compose up -d db
```

Seed the sample database:

```bash
psql postgresql://postgres:postgres@localhost:5432/appdb -f scripts/seed_postgres.sql
```

### 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Explore the API

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

## Example: discover metadata from a real PostgreSQL database

```bash
curl -X POST "http://localhost:8000/api/schema/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales_db",
    "database_url": "postgresql://postgres:postgres@localhost:5432/appdb",
    "dialect": "postgres"
  }'
```

If you set `DATABASE_URL` in your environment, you can omit `database_url` from the request body.

## Seed database schema

The project includes a ready-to-use PostgreSQL seed file at `scripts/seed_postgres.sql`.

It creates:
- `customers`
- `products`
- `orders`

and inserts a small dataset for local prompt generation and SQL testing.

## Docker

Build and run with Docker Compose:

```bash
docker-compose up --build
```

Or build directly:

```bash
docker build -t scientific-db-prompt-writer .
docker run -p 8000:8000 --env DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/appdb scientific-db-prompt-writer
```

## Multi-database source mapping

For multi-database mode, the project computes:

- shared entities across databases
- field overlap mappings
- likely join/merge candidates
- conflict resolution suggestions

## Scientific prompt structure

The generated prompt includes:

- objective
- relevant schema
- scientific method
- search strategy
- constraints
- output requirements
- validation and quality-control guidance

## Testing

```bash
pytest -q
```
