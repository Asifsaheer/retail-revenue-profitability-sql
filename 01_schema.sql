PRAGMA foreign_keys=ON;
CREATE TABLE branches(branch_id INTEGER PRIMARY KEY,branch_name TEXT NOT NULL,city TEXT NOT NULL);
CREATE TABLE products(product_id INTEGER PRIMARY KEY,product_name TEXT NOT NULL,category TEXT NOT NULL,unit_cost_aed REAL NOT NULL CHECK(unit_cost_aed>=0),list_price_aed REAL NOT NULL CHECK(list_price_aed>0));
CREATE TABLE customers(customer_id INTEGER PRIMARY KEY,customer_name TEXT NOT NULL,customer_segment TEXT NOT NULL);
CREATE TABLE orders(order_id INTEGER PRIMARY KEY,customer_id INTEGER NOT NULL REFERENCES customers(customer_id),branch_id INTEGER NOT NULL REFERENCES branches(branch_id),order_date TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('Completed','Cancelled','Returned')));
CREATE TABLE order_items(item_id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(order_id),product_id INTEGER NOT NULL REFERENCES products(product_id),quantity INTEGER NOT NULL CHECK(quantity>0),unit_price_aed REAL NOT NULL CHECK(unit_price_aed>=0),discount_pct REAL NOT NULL CHECK(discount_pct BETWEEN 0 AND 1));
CREATE INDEX idx_orders_date ON orders(order_date); CREATE INDEX idx_orders_branch ON orders(branch_id); CREATE INDEX idx_items_order ON order_items(order_id);
