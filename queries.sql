-- =============================================================================
-- queries.sql
-- All 7 required analytical queries for the Patent Intelligence Pipeline
-- =============================================================================

-- Q1: Top Inventors — Who has filed the most patents?
-- -----------------------------------------------------------------------------
SELECT
    i.inventor_id,
    i.name,
    i.country,
    COUNT(DISTINCT pr.patent_id) AS patent_count
FROM inventors i
JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
GROUP BY i.inventor_id, i.name, i.country
ORDER BY patent_count DESC
LIMIT 20;


-- Q2: Top Companies — Which assignees own the most patents?
-- -----------------------------------------------------------------------------
SELECT
    c.company_id,
    c.name,
    COUNT(DISTINCT pr.patent_id) AS patent_count
FROM companies c
JOIN patent_relationships pr ON c.company_id = pr.company_id
GROUP BY c.company_id, c.name
ORDER BY patent_count DESC
LIMIT 20;


-- Q3: Countries — Which countries produce the most patents?
-- -----------------------------------------------------------------------------
SELECT
    i.country,
    COUNT(DISTINCT pr.patent_id) AS patent_count,
    ROUND(
        COUNT(DISTINCT pr.patent_id) * 100.0 /
        (SELECT COUNT(DISTINCT patent_id) FROM patent_relationships),
        2
    ) AS share_pct
FROM inventors i
JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
WHERE i.country IS NOT NULL
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 20;


-- Q4: Trends Over Time — How many patents per year?
-- -----------------------------------------------------------------------------
SELECT
    year,
    COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year ASC;


-- Q5: JOIN Query — Combine patents with inventors and companies
-- -----------------------------------------------------------------------------
SELECT
    p.patent_id,
    p.title,
    p.year,
    p.filing_date,
    i.name         AS inventor_name,
    i.country      AS inventor_country,
    c.name         AS company_name
FROM patents p
JOIN patent_relationships pr ON p.patent_id = pr.patent_id
JOIN inventors i             ON pr.inventor_id = i.inventor_id
LEFT JOIN companies c        ON pr.company_id = c.company_id
ORDER BY p.year DESC, p.patent_id
LIMIT 500;


-- Q6: CTE Query — Top inventor per country (using WITH)
-- -----------------------------------------------------------------------------
WITH inventor_patent_counts AS (
    -- Step 1: count patents per inventor
    SELECT
        i.inventor_id,
        i.name,
        i.country,
        COUNT(DISTINCT pr.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
    WHERE i.country IS NOT NULL
    GROUP BY i.inventor_id, i.name, i.country
),
country_max AS (
    -- Step 2: find the max patent count per country
    SELECT country, MAX(patent_count) AS max_patents
    FROM inventor_patent_counts
    GROUP BY country
)
-- Step 3: return the top inventor for each country
SELECT
    ipc.country,
    ipc.name        AS top_inventor,
    ipc.patent_count
FROM inventor_patent_counts ipc
JOIN country_max cm
  ON ipc.country = cm.country AND ipc.patent_count = cm.max_patents
ORDER BY ipc.patent_count DESC
LIMIT 30;


-- Q7: Ranking Query — Rank inventors using window functions
-- -----------------------------------------------------------------------------
SELECT
    inventor_id,
    name,
    country,
    patent_count,
    RANK()       OVER (ORDER BY patent_count DESC) AS global_rank,
    DENSE_RANK() OVER (ORDER BY patent_count DESC) AS dense_rank,
    RANK()       OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank,
    ROUND(
        patent_count * 100.0 / SUM(patent_count) OVER (),
        4
    ) AS share_pct
FROM (
    SELECT
        i.inventor_id,
        i.name,
        i.country,
        COUNT(DISTINCT pr.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
    GROUP BY i.inventor_id, i.name, i.country
) ranked_inventors
ORDER BY global_rank
LIMIT 50;
