from app.models import DatabaseSchema, FieldSchema, TableSchema
from app.sql.generator import generate_sql_from_prompt


def test_generate_sql_from_prompt_postgres():
    schema = DatabaseSchema(
        name="sales_db",
        dialect="postgres",
        tables=[
            TableSchema(
                name="orders",
                fields=[
                    FieldSchema(name="order_id", type="integer"),
                    FieldSchema(name="customer_id", type="integer"),
                    FieldSchema(name="amount", type="numeric"),
                    FieldSchema(name="order_date", type="date"),
                ],
            )
        ],
    )
    sql = generate_sql_from_prompt("Show high-value orders in the last month", schema, "postgres")
    assert "SELECT" in sql.upper()
    assert "FROM orders" in sql
    assert "LIMIT 100" in sql


def test_generate_sql_from_prompt_mysql():
    schema = DatabaseSchema(
        name="crm_db",
        dialect="mysql",
        tables=[
            TableSchema(
                name="customers",
                fields=[
                    FieldSchema(name="customer_id", type="integer"),
                    FieldSchema(name="country", type="text"),
                    FieldSchema(name="signup_date", type="date"),
                ],
            )
        ],
    )
    sql = generate_sql_from_prompt("Find recent customers", schema, "mysql")
    assert "FROM `customers`" in sql
    assert "LIMIT 100" in sql
