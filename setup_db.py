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

conn.commit()
print("✓ Database created successfully!")
