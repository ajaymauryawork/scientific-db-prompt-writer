CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100) NOT NULL,
    signup_date DATE NOT NULL,
    segment VARCHAR(50) NOT NULL DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    order_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
);

INSERT INTO customers (first_name, last_name, email, country, signup_date, segment)
VALUES
    ('Ava', 'Patel', 'ava.patel@example.com', 'USA', '2024-01-15', 'vip'),
    ('Liam', 'Khan', 'liam.khan@example.com', 'UK', '2024-02-11', 'new'),
    ('Sofia', 'Martinez', 'sofia.martinez@example.com', 'Spain', '2023-11-20', 'returning'),
    ('Noah', 'Nguyen', 'noah.nguyen@example.com', 'Canada', '2024-03-03', 'new'),
    ('Emma', 'Brown', 'emma.brown@example.com', 'USA', '2023-08-07', 'vip')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (product_name, category, unit_price)
VALUES
    ('Analytics Pro', 'software', 299.99),
    ('Cloud Sync', 'software', 149.50),
    ('Data Studio', 'analytics', 89.00),
    ('Growth Suite', 'platform', 219.00),
    ('Support Plus', 'service', 49.99)
ON CONFLICT DO NOTHING;

INSERT INTO orders (customer_id, product_id, order_date, quantity, amount, status)
VALUES
    (1, 1, '2024-05-10', 2, 599.98, 'completed'),
    (1, 3, '2024-05-16', 1, 89.00, 'completed'),
    (2, 2, '2024-06-01', 3, 448.50, 'pending'),
    (3, 4, '2024-04-20', 1, 219.00, 'completed'),
    (4, 5, '2024-06-05', 2, 99.98, 'completed'),
    (5, 1, '2024-06-07', 1, 299.99, 'completed'),
    (5, 2, '2024-06-12', 4, 598.00, 'completed')
ON CONFLICT DO NOTHING;

SELECT * FROM customers;
SELECT * FROM products;
SELECT * FROM orders;
