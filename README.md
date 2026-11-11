# Retail Revenue & Profitability Analysis | SQL Portfolio

**Role simulated:** Junior Data Analyst / Reporting Analyst  
**Stack:** SQLite, SQL, relational joins, CTEs, window functions, data validation  
**Data:** 100% synthetic, reproducibly generated. Not actual Sahivox or client data.

## Business problem
A fictional UAE retail chain needs a single source of truth for completed sales, branch profitability, product performance, discount exposure, and customer behavior. The goal is to identify where revenue and profit come from and where management should investigate further.

## Data model
- `branches` (4 branches)
- `products` (8 products)
- `customers` (150 customers)
- `orders` (600 orders; completed/cancelled/returned)
- `order_items` (multiple products per order)

Relationships: `orders.customer_id -> customers.customer_id`; `orders.branch_id -> branches.branch_id`; `order_items.order_id -> orders.order_id`; `order_items.product_id -> products.product_id`.

## Run it
1. Install SQLite or use the SQLite extension in VS Code / DBeaver.
2. Open `retail_analytics.db` (the data and `sales_lines` view are already loaded).
3. Run individual queries from `03_business_analysis.sql`.
4. To regenerate the dataset from scratch: `python generate_data.py` (Python 3 standard library only).

## Business rules and limitations
- Revenue and gross profit include **completed orders only**; cancelled and returned orders are excluded (not modeled as negative refund transactions).
- Revenue = quantity × unit price × (1 - discount); COGS = quantity × unit cost; gross profit = revenue - COGS.
- Currency AED. Margin = gross profit / revenue. Results are illustrative, not real financial claims.
- Monthly periods are calendar months; the last month is partial (Jul 1–Oct 28, 2026). Avoid interpreting partial-month trends as full-month changes.
- Data is synthetic, so correlations are not proof of causal impact.

## Verified sample results (generated data)
- Completed orders: **560**
- Net sales: **AED 376,639.15**
- Gross profit: **AED 167,291.15**
- Gross margin: **44.42%**
- Highest revenue branch: **Dubai Mall** (AED 131,721.85)
- Highest gross-profit product: **Study Desk** (AED 53,282.50)

## Analysis questions (16 queries)
1. Total revenue, profit, margin, and AOV
2. Branch profitability
3. Product profitability
4. Monthly revenue and MoM growth using `LAG()`
5. Top customers
6. Discount band margin comparison
7. Order status mix
8. Branch × category revenue
9. Product rankings using `DENSE_RANK()`
10. Repeat customer rate
11. Branch revenue share using window functions
12. Order value distribution
13. Weighted discount by branch
14. Lowest-margin products
15. Weekday revenue
16. Referential integrity and quality checks

## Suggested management decisions
- Review branch revenue **and** margin before reallocating marketing spend; revenue alone is insufficient.
- Investigate products with low gross margins before changing prices; consider unit economics and customer demand.
- Examine discount bands for potential margin dilution; do not infer discounts caused a change from observational data.

## Files
- `01_schema.sql`: normalized tables, constraints, indexes
- `02_sales_view.sql`: reusable metric definitions
- `03_business_analysis.sql`: 16 documented analytical queries
- `retail_analytics.db`: ready-to-run SQLite database
- `generate_data.py`: reproducible data generation

## Resume bullet (use after you run and understand the project)
**Retail Revenue & Profitability Analysis | SQL, SQLite:** Built a 5-table relational retail database and wrote 16 business queries using joins, CTEs, `LAG`, `DENSE_RANK`, and KPI calculations to evaluate branch revenue, product margins, discounts, and repeat customers on synthetic UAE retail data.

## Next improvements
- Add screenshots of actual SQL outputs to `screenshots/`.
- Connect Power BI to the data and create a one-page executive dashboard.
- Add a short `insights.md` explaining 3 findings with exact query output and business recommendations.
