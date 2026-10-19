-- ARCHIVED DRAFT: under revision, not evidence of professional delivery.
-- Unvalidated illustrative code; not a production implementation or compliance tool.
-- =========================================================================================
-- PROJECT: ENTERPRISE FINANCIAL TRANSACTIONS & REVENUE COHORT ANALYTICS
-- AUTHOR: Nguyen Thi Xuan Hien | Business Intelligence & Data Analytics
-- DATABASE: PostgreSQL 14+ / ANSI SQL Compatible
-- SCRIPT 02: ADVANCED CUSTOMER COHORT RETENTION & RFM SEGMENTATION ENGINE
-- =========================================================================================

SET search_path TO analytics_dw, public;

-- =========================================================================================
-- 1. MONTHLY COHORT RETENTION ANALYSIS (TRIANGULAR MATRIX)
-- Business Goal: Measure long-term customer stickiness and repeat purchase decay.
-- =========================================================================================

WITH customer_first_purchase AS (
    -- Identify the inception cohort month for every individual customer
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(order_date))::DATE AS cohort_month
    FROM fact_orders
    WHERE order_status = 'Completed'
    GROUP BY customer_id
),

customer_monthly_activity AS (
    -- Map each customer purchase to an elapsed month index relative to their first purchase
    SELECT 
        o.customer_id,
        cfp.cohort_month,
        DATE_TRUNC('month', o.order_date)::DATE AS activity_month,
        (
            (EXTRACT(YEAR FROM o.order_date) - EXTRACT(YEAR FROM cfp.cohort_month)) * 12 +
            (EXTRACT(MONTH FROM o.order_date) - EXTRACT(MONTH FROM cfp.cohort_month))
        )::INTEGER AS month_number,
        SUM(o.net_revenue_usd) AS monthly_revenue
    FROM fact_orders o
    INNER JOIN customer_first_purchase cfp ON o.customer_id = cfp.customer_id
    WHERE o.order_status = 'Completed'
    GROUP BY 
        o.customer_id, 
        cfp.cohort_month, 
        DATE_TRUNC('month', o.order_date)::DATE,
        EXTRACT(YEAR FROM o.order_date),
        EXTRACT(MONTH FROM o.order_date)
),

cohort_size AS (
    -- Count baseline cohort volume (Month 0 population)
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) AS total_cohort_customers
    FROM customer_first_purchase
    GROUP BY cohort_month
),

cohort_retention_summary AS (
    -- Aggregate active retaining customers and revenue per cohort per elapsed month
    SELECT 
        cma.cohort_month,
        cs.total_cohort_customers,
        cma.month_number,
        COUNT(DISTINCT cma.customer_id) AS active_customers,
        ROUND((COUNT(DISTINCT cma.customer_id)::NUMERIC / cs.total_cohort_customers) * 100, 2) AS retention_rate_pct,
        ROUND(SUM(cma.monthly_revenue), 2) AS cohort_revenue_usd
    FROM customer_monthly_activity cma
    INNER JOIN cohort_size cs ON cma.cohort_month = cs.cohort_month
    GROUP BY cma.cohort_month, cs.total_cohort_customers, cma.month_number
)

-- Final Pivot-friendly Cohort Retention Output
SELECT 
    TO_CHAR(cohort_month, 'YYYY-MM') AS cohort_cohort_label,
    total_cohort_customers,
    MAX(CASE WHEN month_number = 0 THEN retention_rate_pct END) AS m0_retention_pct,
    MAX(CASE WHEN month_number = 1 THEN retention_rate_pct END) AS m1_retention_pct,
    MAX(CASE WHEN month_number = 2 THEN retention_rate_pct END) AS m2_retention_pct,
    MAX(CASE WHEN month_number = 3 THEN retention_rate_pct END) AS m3_retention_pct,
    MAX(CASE WHEN month_number = 6 THEN retention_rate_pct END) AS m6_retention_pct,
    MAX(CASE WHEN month_number = 12 THEN retention_rate_pct END) AS m12_retention_pct
FROM cohort_retention_summary
GROUP BY cohort_month, total_cohort_customers
ORDER BY cohort_month DESC;


-- =========================================================================================
-- 2. ADVANCED RFM (RECENCY, FREQUENCY, MONETARY) SEGMENTATION ENGINE
-- Business Goal: Categorize customers into actionable lifecycle personas for marketing/finance.
-- =========================================================================================

WITH rfm_raw_metrics AS (
    -- Step A: Compute raw Recency (days since last order), Frequency (order count), and Monetary (LTV)
    SELECT 
        c.customer_id,
        c.customer_code,
        c.customer_name,
        c.segment AS market_segment,
        MAX(o.order_date) AS last_order_date,
        -- Reference date set to current evaluation snapshot
        ('2026-10-01'::DATE - MAX(o.order_date)::DATE) AS recency_days,
        COUNT(DISTINCT o.order_id) AS total_orders_frequency,
        COALESCE(SUM(o.net_revenue_usd), 0.00) AS total_spend_monetary
    FROM dim_customers c
    INNER JOIN fact_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Completed'
    GROUP BY c.customer_id, c.customer_code, c.customer_name, c.segment
),

rfm_percentile_scores AS (
    -- Step B: Assign quintile scores (1 to 5) using statistical window functions NTILE(5)
    -- Recency: Lower days = Higher score (NTILE inverted)
    -- Frequency & Monetary: Higher value = Higher score
    SELECT 
        customer_id,
        customer_code,
        customer_name,
        market_segment,
        recency_days,
        total_orders_frequency,
        total_spend_monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY total_orders_frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY total_spend_monetary ASC) AS m_score
    FROM rfm_raw_metrics
),

rfm_composite AS (
    -- Step C: Calculate composite score and concatenate strings for segment tagging
    SELECT 
        *,
        (r_score + f_score + m_score) AS composite_score,
        CONCAT(r_score::TEXT, f_score::TEXT, m_score::TEXT) AS rfm_cell
    FROM rfm_percentile_scores
)

-- Step D: Map statistical scores into strategic executive personas
SELECT 
    customer_id,
    customer_code,
    customer_name,
    market_segment,
    recency_days,
    total_orders_frequency,
    total_spend_monetary,
    r_score,
    f_score,
    m_score,
    CASE 
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions / VIPs'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Core Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New / High Potential'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'At Risk (High Spender Dormant)'
        WHEN r_score = 1 AND f_score <= 2 THEN 'Churned / Lost'
        ELSE 'Developing / Standard'
    END AS customer_lifecycle_segment,
    ROUND((total_spend_monetary / NULLIF(total_orders_frequency, 0)), 2) AS average_order_value_usd
FROM rfm_composite
ORDER BY total_spend_monetary DESC;
