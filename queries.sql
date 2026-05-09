-- queries.sql
-- Global Patent Intelligence — All 7 Required Analytical Queries
-- Each query can be run independently in any SQLite client.

-- ══════════════════════════════════════════════════════════════
-- Q1: Top Inventors — Who has the most patents?
-- ══════════════════════════════════════════════════════════════
SELECT
    i.name,
    i.country,
    COUNT(DISTINCT pi.patent_id) AS patent_count
FROM inventors i
JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
GROUP BY i.inventor_id, i.name, i.country
ORDER BY patent_count DESC
LIMIT 20;


-- ══════════════════════════════════════════════════════════════
-- Q2: Top Companies — Which companies own the most patents?
-- ══════════════════════════════════════════════════════════════
SELECT
    c.name               AS company,
    c.country,
    COUNT(DISTINCT pc.patent_id) AS patent_count
FROM companies c
JOIN patent_companies pc ON c.company_id = pc.company_id
GROUP BY c.company_id, c.name, c.country
ORDER BY patent_count DESC
LIMIT 20;


-- ══════════════════════════════════════════════════════════════
-- Q3: Countries — Which countries produce the most patents?
-- ══════════════════════════════════════════════════════════════
SELECT
    i.country,
    COUNT(DISTINCT pi.patent_id) AS patent_count,
    ROUND(
        COUNT(DISTINCT pi.patent_id) * 100.0 /
        (SELECT COUNT(*) FROM patent_inventors),
        2
    ) AS share_pct
FROM inventors i
JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
WHERE i.country != 'UNKNOWN'
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 20;


-- ══════════════════════════════════════════════════════════════
-- Q4: Trends Over Time — Patent counts per year
-- ══════════════════════════════════════════════════════════════
SELECT
    year,
    COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;


-- ══════════════════════════════════════════════════════════════
-- Q5: JOIN Query — Patents with their inventors and companies
-- ══════════════════════════════════════════════════════════════
SELECT
    p.patent_id,
    p.title,
    p.filing_date,
    p.year,
    i.name        AS inventor_name,
    i.country     AS inventor_country,
    c.name        AS company_name
FROM patents p
LEFT JOIN patent_inventors pi ON p.patent_id = pi.patent_id
LEFT JOIN inventors i         ON pi.inventor_id = i.inventor_id
LEFT JOIN patent_companies pc ON p.patent_id = pc.patent_id
LEFT JOIN companies c         ON pc.company_id = c.company_id
ORDER BY p.year DESC, p.patent_id
LIMIT 500;


-- ══════════════════════════════════════════════════════════════
-- Q6: CTE Query — Multi-step: active inventors per country per year
-- ══════════════════════════════════════════════════════════════
WITH inventor_years AS (
    -- Step 1: find the year each patent-inventor pair was filed
    SELECT
        i.inventor_id,
        i.country,
        p.year
    FROM inventors i
    JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
    JOIN patents p            ON pi.patent_id = p.patent_id
    WHERE p.year IS NOT NULL
      AND i.country != 'UNKNOWN'
),
country_year_activity AS (
    -- Step 2: count unique active inventors per country per year
    SELECT
        country,
        year,
        COUNT(DISTINCT inventor_id) AS active_inventors,
        COUNT(*)                    AS total_patents
    FROM inventor_years
    GROUP BY country, year
)
-- Step 3: return results ordered by year then activity
SELECT
    country,
    year,
    active_inventors,
    total_patents,
    ROUND(total_patents * 1.0 / active_inventors, 2) AS patents_per_inventor
FROM country_year_activity
ORDER BY year DESC, total_patents DESC
LIMIT 100;


-- ══════════════════════════════════════════════════════════════
-- Q7: Ranking Query — Rank inventors using window functions
-- ══════════════════════════════════════════════════════════════
WITH inventor_counts AS (
    SELECT
        i.inventor_id,
        i.name,
        i.country,
        COUNT(DISTINCT pi.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
    GROUP BY i.inventor_id, i.name, i.country
)
SELECT
    RANK()       OVER (ORDER BY patent_count DESC)                   AS global_rank,
    DENSE_RANK() OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank,
    name,
    country,
    patent_count,
    ROUND(
        patent_count * 100.0 / SUM(patent_count) OVER (),
        4
    ) AS pct_of_total
FROM inventor_counts
ORDER BY global_rank
LIMIT 50;
