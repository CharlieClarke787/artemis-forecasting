import sqlite3
from datetime import datetime

# Create database file
conn = sqlite3.connect('forecasts.db')
c = conn.cursor()

# Create tables (like spreadsheet tabs)
c.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    text TEXT,
    type TEXT,
    created_at TEXT
    ,source TEXT DEFAULT 'Manual'
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY,
    question_id INTEGER,
    forecaster TEXT,
    probability REAL,
    rationale TEXT,
    created_at TEXT,
    FOREIGN KEY(question_id) REFERENCES questions(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS ground_truth (
    id INTEGER PRIMARY KEY,
    question_id INTEGER,
    outcome INTEGER,
    resolved_at TEXT,
    FOREIGN KEY(question_id) REFERENCES questions(id)
)
''')

c.execute('''CREATE TABLE IF NOT EXISTS report_snapshots (
    id INTEGER PRIMARY KEY, source_url TEXT NOT NULL, report_title TEXT,
    report_date TEXT, content_hash TEXT NOT NULL UNIQUE, generator_version TEXT NOT NULL,
    retrieved_at TEXT NOT NULL, assumptions TEXT NOT NULL
)''')
c.execute('''CREATE TABLE IF NOT EXISTS draft_forecasts (
    id INTEGER PRIMARY KEY, snapshot_id INTEGER NOT NULL, question TEXT NOT NULL,
    probability REAL NOT NULL CHECK(probability >= 0 AND probability <= 1),
    rationale TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unapproved',
    reviewed_by TEXT, reviewed_at TEXT, review_notes TEXT,
    UNIQUE(snapshot_id, question), FOREIGN KEY(snapshot_id) REFERENCES report_snapshots(id)
)''')

conn.commit()
print("✓ Database created successfully!")
