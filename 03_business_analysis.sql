-- Q01 Overall KPIs
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
