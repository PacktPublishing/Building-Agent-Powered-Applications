-- customer table
CREATE TABLE customers (customer_id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100));

-- order table
CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id INT,
    order_date DATE, total_amount DECIMAL(10, 2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- order ite
CREATE TABLE order_items (item_id INT PRIMARY KEY, order_id INT, product_name VARCHAR(100),
    quantity INT, price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);