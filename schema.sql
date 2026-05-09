-- schema.sql
-- Global Patent Intelligence — SQLite Database Schema
-- Run automatically by 03_load_db.py

PRAGMA foreign_keys = ON;

-- ── Core tables ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS patents (
    patent_id    TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    abstract     TEXT,
    filing_date  TEXT,
    year         INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    country      TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    country      TEXT
);

-- ── Relationship tables ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS patent_inventors (
    patent_id    TEXT NOT NULL REFERENCES patents(patent_id),
    inventor_id  TEXT NOT NULL REFERENCES inventors(inventor_id),
    PRIMARY KEY (patent_id, inventor_id)
);

CREATE TABLE IF NOT EXISTS patent_companies (
    patent_id    TEXT NOT NULL REFERENCES patents(patent_id),
    company_id   TEXT NOT NULL REFERENCES companies(company_id),
    PRIMARY KEY (patent_id, company_id)
);

-- ── Indexes for faster query performance ─────────────────────

CREATE INDEX IF NOT EXISTS idx_patents_year        ON patents(year);
CREATE INDEX IF NOT EXISTS idx_inventors_country   ON inventors(country);
CREATE INDEX IF NOT EXISTS idx_companies_country   ON companies(country);
CREATE INDEX IF NOT EXISTS idx_pi_inventor         ON patent_inventors(inventor_id);
CREATE INDEX IF NOT EXISTS idx_pc_company          ON patent_companies(company_id);
