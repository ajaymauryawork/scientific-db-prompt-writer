{
  "databases": [
    {
      "name": "sales_db",
      "dialect": "postgres",
      "tables": [
        {
          "name": "customers",
          "fields": [
            {"name": "customer_id", "type": "integer"},
            {"name": "country", "type": "text"},
            {"name": "signup_date", "type": "date"}
          ]
        },
        {
          "name": "orders",
          "fields": [
            {"name": "order_id", "type": "integer"},
            {"name": "customer_id", "type": "integer"},
            {"name": "order_date", "type": "date"},
            {"name": "amount", "type": "numeric"}
          ]
        }
      ]
    }
  ]
}
