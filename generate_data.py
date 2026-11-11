import sqlite3,random,datetime,pathlib,zipfile
p=pathlib.Path(__file__).resolve().parent;random.seed(42)
(p/'retail_analytics.db').unlink(missing_ok=True)
conn=sqlite3.connect(p/'retail_analytics.db');c=conn.cursor()
schema='''PRAGMA foreign_keys=ON;
CREATE TABLE branches(branch_id INTEGER PRIMARY KEY,branch_name TEXT NOT NULL,city TEXT NOT NULL);
CREATE TABLE products(product_id INTEGER PRIMARY KEY,product_name TEXT NOT NULL,category TEXT NOT NULL,unit_cost_aed REAL NOT NULL CHECK(unit_cost_aed>=0),list_price_aed REAL NOT NULL CHECK(list_price_aed>0));
CREATE TABLE customers(customer_id INTEGER PRIMARY KEY,customer_name TEXT NOT NULL,customer_segment TEXT NOT NULL);
CREATE TABLE orders(order_id INTEGER PRIMARY KEY,customer_id INTEGER NOT NULL REFERENCES customers(customer_id),branch_id INTEGER NOT NULL REFERENCES branches(branch_id),order_date TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('Completed','Cancelled','Returned')));
CREATE TABLE order_items(item_id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(order_id),product_id INTEGER NOT NULL REFERENCES products(product_id),quantity INTEGER NOT NULL CHECK(quantity>0),unit_price_aed REAL NOT NULL CHECK(unit_price_aed>=0),discount_pct REAL NOT NULL CHECK(discount_pct BETWEEN 0 AND 1));
CREATE INDEX idx_orders_date ON orders(order_date); CREATE INDEX idx_orders_branch ON orders(branch_id); CREATE INDEX idx_items_order ON order_items(order_id);
'''
(p/'01_schema.sql').write_text(schema);c.executescript(schema)
branches=[(1,'Dubai Mall','Dubai'),(2,'Deira','Dubai'),(3,'Sharjah Central','Sharjah'),(4,'Abu Dhabi Corniche','Abu Dhabi')]
products=[(1,'Office Chair','Furniture',250,420),(2,'Desk Lamp','Electronics',60,110),(3,'Notebook','Stationery',7,18),(4,'Water Bottle','Accessories',20,45),(5,'Monitor Stand','Accessories',45,95),(6,'Wireless Mouse','Electronics',35,85),(7,'Study Desk','Furniture',180,350),(8,'USB Hub','Electronics',25,65)]
c.executemany('INSERT INTO branches VALUES(?,?,?)',branches);c.executemany('INSERT INTO products VALUES(?,?,?,?,?)',products)
customers=[(i,f'Customer {i:03d}',random.choice(['Retail','Small Business','Corporate'])) for i in range(1,151)];c.executemany('INSERT INTO customers VALUES(?,?,?)',customers)
orders=[];items=[];iid=1;start=datetime.date(2026,7,1)
for oid in range(1,601):
    day=start+datetime.timedelta(days=random.randrange(120));status=random.choices(['Completed','Cancelled','Returned'],[.92,.05,.03])[0];branch=random.choices([1,2,3,4],[.35,.20,.25,.20])[0]
    orders.append((oid,random.randrange(1,151),branch,day.isoformat(),status))
    for _ in range(random.randint(1,3)):
        product=random.choice(products);pid=product[0];qty=random.randint(1,4);disc=random.choices([0,.05,.10,.15,.20],[.45,.2,.18,.12,.05])[0]
        items.append((iid,oid,pid,qty,product[4],disc));iid+=1
c.executemany('INSERT INTO orders VALUES(?,?,?,?,?)',orders);c.executemany('INSERT INTO order_items VALUES(?,?,?,?,?,?)',items);conn.commit()
view='''-- Completed sales only; cancelled and returned orders are excluded.
-- Revenue = quantity * unit price * (1-discount); COGS = quantity * unit cost.
CREATE VIEW sales_lines AS
SELECT o.order_id,o.order_date,o.branch_id,o.customer_id,i.product_id,i.quantity,i.discount_pct,
 ROUND(i.quantity*i.unit_price_aed*(1-i.discount_pct),2) AS revenue_aed,
 ROUND(i.quantity*p.unit_cost_aed,2) AS cogs_aed,
 ROUND(i.quantity*i.unit_price_aed*(1-i.discount_pct)-i.quantity*p.unit_cost_aed,2) AS gross_profit_aed
FROM orders o JOIN order_items i ON i.order_id=o.order_id JOIN products p ON p.product_id=i.product_id
WHERE o.status='Completed';
''';(p/'02_sales_view.sql').write_text(view);c.executescript(view)
queries='''-- Q01 Overall KPIs
SELECT COUNT(DISTINCT order_id) AS completed_orders,ROUND(SUM(revenue_aed),2) AS revenue_aed,
 ROUND(SUM(cogs_aed),2) AS cogs_aed,ROUND(SUM(gross_profit_aed),2) AS gross_profit_aed,
 ROUND(100.0*SUM(gross_profit_aed)/NULLIF(SUM(revenue_aed),0),2) AS gross_margin_pct,
 ROUND(SUM(revenue_aed)/NULLIF(COUNT(DISTINCT order_id),0),2) AS aov_aed
FROM sales_lines;

-- Q02 Branch revenue and margin
SELECT b.branch_name,ROUND(SUM(s.revenue_aed),2) AS revenue_aed,
 ROUND(SUM(s.gross_profit_aed),2) AS gross_profit_aed,
 ROUND(100.0*SUM(s.gross_profit_aed)/NULLIF(SUM(s.revenue_aed),0),2) AS gross_margin_pct
FROM sales_lines s JOIN branches b ON s.branch_id=b.branch_id
GROUP BY b.branch_id,b.branch_name ORDER BY revenue_aed DESC;

-- Q03 Product profitability (note revenue rank differs from margin rank)
SELECT p.product_name,p.category,SUM(s.quantity) AS units,
 ROUND(SUM(s.revenue_aed),2) AS revenue_aed,ROUND(SUM(s.gross_profit_aed),2) AS gross_profit_aed,
 ROUND(100.0*SUM(s.gross_profit_aed)/NULLIF(SUM(s.revenue_aed),0),2) AS gross_margin_pct
FROM sales_lines s JOIN products p ON s.product_id=p.product_id
GROUP BY p.product_id,p.product_name,p.category ORDER BY gross_profit_aed DESC;

-- Q04 Monthly revenue trend and month-over-month growth using LAG
WITH monthly AS (
 SELECT substr(order_date,1,7) AS month,ROUND(SUM(revenue_aed),2) AS revenue_aed
 FROM sales_lines GROUP BY substr(order_date,1,7)
), trend AS (
 SELECT month,revenue_aed,LAG(revenue_aed) OVER(ORDER BY month) AS prior_month_aed FROM monthly
)
SELECT month,revenue_aed,prior_month_aed,
 ROUND(100.0*(revenue_aed-prior_month_aed)/NULLIF(prior_month_aed,0),2) AS mom_growth_pct
FROM trend ORDER BY month;

-- Q05 Top 10 customers by revenue
SELECT c.customer_id,c.customer_segment,COUNT(DISTINCT s.order_id) AS orders,
 ROUND(SUM(s.revenue_aed),2) AS revenue_aed
FROM sales_lines s JOIN customers c ON s.customer_id=c.customer_id
GROUP BY c.customer_id,c.customer_segment ORDER BY revenue_aed DESC LIMIT 10;

-- Q06 Discount bands and gross margin
SELECT CASE WHEN discount_pct=0 THEN '0%' WHEN discount_pct<=0.05 THEN '1-5%'
 WHEN discount_pct<=0.10 THEN '6-10%' WHEN discount_pct<=0.15 THEN '11-15%' ELSE '16-20%' END AS discount_band,
 COUNT(*) AS line_items,ROUND(SUM(revenue_aed),2) AS revenue_aed,
 ROUND(100.0*SUM(gross_profit_aed)/NULLIF(SUM(revenue_aed),0),2) AS gross_margin_pct
FROM sales_lines GROUP BY discount_band ORDER BY MIN(discount_pct);

-- Q07 Status mix (quality/operations)
SELECT status,COUNT(*) AS orders,ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM orders),2) AS share_pct
FROM orders GROUP BY status ORDER BY orders DESC;

-- Q08 Revenue by category and branch
SELECT b.branch_name,p.category,ROUND(SUM(s.revenue_aed),2) AS revenue_aed
FROM sales_lines s JOIN branches b ON s.branch_id=b.branch_id JOIN products p ON s.product_id=p.product_id
GROUP BY b.branch_id,b.branch_name,p.category ORDER BY b.branch_name,revenue_aed DESC;

-- Q09 Rank products within each category by gross profit
WITH product_profit AS (
 SELECT p.category,p.product_name,ROUND(SUM(s.gross_profit_aed),2) AS profit_aed
 FROM sales_lines s JOIN products p ON s.product_id=p.product_id
 GROUP BY p.category,p.product_id,p.product_name
)
SELECT category,product_name,profit_aed,DENSE_RANK() OVER(PARTITION BY category ORDER BY profit_aed DESC) AS category_rank
FROM product_profit ORDER BY category,category_rank;

-- Q10 Repeat customers (2+ completed orders)
WITH customer_orders AS (
 SELECT customer_id,COUNT(DISTINCT order_id) AS order_count FROM sales_lines GROUP BY customer_id
)
SELECT COUNT(*) AS active_customers,
 SUM(CASE WHEN order_count>=2 THEN 1 ELSE 0 END) AS repeat_customers,
 ROUND(100.0*SUM(CASE WHEN order_count>=2 THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS repeat_customer_pct
FROM customer_orders;

-- Q11 Branch share of revenue using window function
WITH branch_sales AS (
 SELECT b.branch_name,SUM(s.revenue_aed) AS revenue_aed FROM sales_lines s
 JOIN branches b ON s.branch_id=b.branch_id GROUP BY b.branch_id,b.branch_name
)
SELECT branch_name,ROUND(revenue_aed,2) AS revenue_aed,
 ROUND(100.0*revenue_aed/NULLIF(SUM(revenue_aed) OVER(),0),2) AS revenue_share_pct
FROM branch_sales ORDER BY revenue_aed DESC;

-- Q12 Order size distribution
WITH order_totals AS (
 SELECT order_id,SUM(revenue_aed) AS order_revenue FROM sales_lines GROUP BY order_id
)
SELECT CASE WHEN order_revenue<200 THEN 'Under 200' WHEN order_revenue<500 THEN '200-499'
 WHEN order_revenue<1000 THEN '500-999' ELSE '1000+' END AS order_value_band,
 COUNT(*) AS order_count,ROUND(AVG(order_revenue),2) AS avg_order_value_aed
FROM order_totals GROUP BY order_value_band ORDER BY MIN(order_revenue);

-- Q13 Average discount by branch (weighted by undiscounted line value)
SELECT b.branch_name,
 ROUND(100.0*SUM(s.quantity*p.list_price_aed*s.discount_pct)/NULLIF(SUM(s.quantity*p.list_price_aed),0),2) AS weighted_discount_pct
FROM sales_lines s JOIN branches b ON s.branch_id=b.branch_id
JOIN products p ON s.product_id=p.product_id GROUP BY b.branch_id,b.branch_name ORDER BY weighted_discount_pct DESC;

-- Q14 Low-margin products for pricing review
SELECT p.product_name,ROUND(SUM(s.revenue_aed),2) AS revenue_aed,
 ROUND(100.0*SUM(s.gross_profit_aed)/NULLIF(SUM(s.revenue_aed),0),2) AS gross_margin_pct
FROM sales_lines s JOIN products p ON s.product_id=p.product_id
GROUP BY p.product_id,p.product_name HAVING SUM(s.revenue_aed)>0
ORDER BY gross_margin_pct ASC LIMIT 5;

-- Q15 Weekday sales (SQLite strftime: 0=Sunday)
SELECT CASE strftime('%w',order_date) WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday'
 WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday'
 WHEN '5' THEN 'Friday' ELSE 'Saturday' END AS weekday,
 COUNT(DISTINCT order_id) AS orders,ROUND(SUM(revenue_aed),2) AS revenue_aed
FROM sales_lines GROUP BY strftime('%w',order_date) ORDER BY strftime('%w',order_date);

-- Q16 Data validation: expect zero rows
SELECT i.item_id FROM order_items i LEFT JOIN orders o ON i.order_id=o.order_id
LEFT JOIN products p ON i.product_id=p.product_id
WHERE o.order_id IS NULL OR p.product_id IS NULL OR i.quantity<=0 OR i.discount_pct NOT BETWEEN 0 AND 1;
''';(p/'03_business_analysis.sql').write_text(queries)
result=c.execute('SELECT COUNT(DISTINCT order_id),ROUND(SUM(revenue_aed),2),ROUND(SUM(gross_profit_aed),2),ROUND(100.0*SUM(gross_profit_aed)/SUM(revenue_aed),2) FROM sales_lines').fetchone()
branchres=c.execute('SELECT b.branch_name,ROUND(SUM(s.revenue_aed),2) FROM sales_lines s JOIN branches b ON s.branch_id=b.branch_id GROUP BY b.branch_id ORDER BY 2 DESC').fetchall()
productres=c.execute('SELECT p.product_name,ROUND(SUM(s.gross_profit_aed),2) FROM sales_lines s JOIN products p ON s.product_id=p.product_id GROUP BY p.product_id ORDER BY 2 DESC LIMIT 1').fetchone()

conn.close()
