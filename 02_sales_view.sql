-- Completed sales only; cancelled and returned orders are excluded.
-- Revenue = quantity * unit price * (1-discount); COGS = quantity * unit cost.
CREATE VIEW sales_lines AS
SELECT o.order_id,o.order_date,o.branch_id,o.customer_id,i.product_id,i.quantity,i.discount_pct,
 ROUND(i.quantity*i.unit_price_aed*(1-i.discount_pct),2) AS revenue_aed,
 ROUND(i.quantity*p.unit_cost_aed,2) AS cogs_aed,
 ROUND(i.quantity*i.unit_price_aed*(1-i.discount_pct)-i.quantity*p.unit_cost_aed,2) AS gross_profit_aed
FROM orders o JOIN order_items i ON i.order_id=o.order_id JOIN products p ON p.product_id=i.product_id
WHERE o.status='Completed';
