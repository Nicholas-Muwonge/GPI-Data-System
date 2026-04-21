-- =============================================================================
-- schema.sql
-- Global Patent Intelligence Database Schema
-- =============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- -----------------------------------------------------------------------------
-- Core tables
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS patents (
    patent_id    TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    abstract     TEXT,
    filing_date  TEXT,               -- stored as YYYY-MM-DD
    year         INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    country      TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- Relationships table  (patent ↔ inventor ↔ company)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS patent_relationships (
    patent_id    TEXT NOT NULL,
    inventor_id  TEXT NOT NULL,
    company_id   TEXT,               -- nullable: some patents have no assignee
    PRIMARY KEY (patent_id, inventor_id, company_id),
    FOREIGN KEY (patent_id)   REFERENCES patents(patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
    FOREIGN KEY (company_id)  REFERENCES companies(company_id)
);

-- -----------------------------------------------------------------------------
-- Indexes for query performance
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_patents_year          ON patents(year);
CREATE INDEX IF NOT EXISTS idx_inventors_country     ON inventors(country);
CREATE INDEX IF NOT EXISTS idx_rel_patent_id         ON patent_relationships(patent_id);
CREATE INDEX IF NOT EXISTS idx_rel_inventor_id       ON patent_relationships(inventor_id);
CREATE INDEX IF NOT EXISTS idx_rel_company_id        ON patent_relationships(company_id);
