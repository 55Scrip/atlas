PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atlas_id TEXT UNIQUE NOT NULL,
    ticker TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    exchange TEXT,
    country TEXT,
    currency TEXT DEFAULT 'USD',
    sector TEXT,
    industry TEXT,
    status TEXT DEFAULT 'Active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    fiscal_year INTEGER NOT NULL,
    revenue REAL,
    gross_profit REAL,
    operating_income REAL,
    net_income REAL,
    operating_cashflow REAL,
    capex REAL,
    free_cashflow REAL,
    total_assets REAL,
    equity REAL,
    debt REAL,
    cash REAL,
    shares_outstanding REAL,
    source_id INTEGER,
    UNIQUE(company_id, fiscal_year),
    FOREIGN KEY(company_id) REFERENCES companies(id),
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    price REAL,
    market_cap REAL,
    enterprise_value REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS valuation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    valuation_date TEXT DEFAULT CURRENT_TIMESTAMP,
    fair_value REAL,
    buy_price REAL,
    strong_buy_price REAL,
    dream_price REAL,
    wacc REAL,
    terminal_growth REAL,
    notes TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS scoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    score_date TEXT DEFAULT CURRENT_TIMESTAMP,
    business_score REAL,
    financial_score REAL,
    technology_score REAL,
    moat_score REAL,
    valuation_score REAL,
    risk_score REAL,
    conviction REAL,
    atlas_score REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS risk_register (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    risk_name TEXT NOT NULL,
    probability REAL,
    impact REAL,
    mitigation TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    title TEXT NOT NULL,
    source_type TEXT,
    url TEXT,
    publication_date TEXT,
    notes TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS research_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    note_type TEXT,
    title TEXT NOT NULL,
    body TEXT,
    confidence TEXT DEFAULT 'Hypothesis',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);
