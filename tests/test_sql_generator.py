from app.models import DatabaseSchema, FieldSchema, TableSchema
from app.prompting.prompt_writer import generate_prompt, generate_source_mapping


def build_example_schema():
    return [
        DatabaseSchema(
            name="sales_db",
            dialect="postgres",
            tables=[
                TableSchema(
                    name="customers",
                    fields=[
                        FieldSchema(name="customer_id", type="integer"),
                        FieldSchema(name="country", type="text"),
                        FieldSchema(name="signup_date", type="date"),
                    ],
                ),
                TableSchema(
                    name="orders",
                    fields=[
                        FieldSchema(name="order_id", type="integer"),
                        FieldSchema(name="customer_id", type="integer"),
                        FieldSchema(name="amount", type="numeric"),
                    ],
                ),
            ],
        ),
        DatabaseSchema(
            name="crm_db",
            dialect="mysql",
            tables=[
                TableSchema(
                    name="accounts",
                    fields=[
                        FieldSchema(name="customer_id", type="integer"),
                        FieldSchema(name="country", type="text"),
                    ],
                ),
                TableSchema(
                    name="transactions",
                    fields=[
                        FieldSchema(name="customer_id", type="integer"),
                        FieldSchema(name="total_amount", type="numeric"),
                    ],
                ),
            ],
        ),
    ]


def test_generate_prompt_single_db():
    dbs = build_example_schema()
    prompt = generate_prompt("Find customers with high-value orders in Europe", dbs[:1], mode="single")
    assert "Objective" in prompt
    assert "customers" in prompt.lower()
    assert "scientific" in prompt.lower()


def test_generate_prompt_multi_db_and_mapping():
    dbs = build_example_schema()
    prompt = generate_prompt("Compare customer value across systems", dbs, mode="multi")
    mapping = generate_source_mapping(dbs)
    assert "cross-database" in prompt.lower()
    assert "shared_fields" in mapping
    assert mapping["mapping_summary"]["database_count"] == 2

