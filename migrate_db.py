import sqlite3

# Add source column to questions table if it doesn't exist
conn = sqlite3.connect('forecasts.db')
c = conn.cursor()

try:
    c.execute('ALTER TABLE questions ADD COLUMN source TEXT DEFAULT "Manual"')
    conn.commit()
    print("[+] Added 'source' column to questions table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("[+] Source column already exists")
    else:
        raise

for statement in (
    '''CREATE TABLE IF NOT EXISTS report_snapshots (
        id INTEGER PRIMARY KEY, source_url TEXT NOT NULL, report_title TEXT,
        report_date TEXT, content_hash TEXT NOT NULL UNIQUE, generator_version TEXT NOT NULL,
        retrieved_at TEXT NOT NULL, assumptions TEXT NOT NULL)''',
    '''CREATE TABLE IF NOT EXISTS draft_forecasts (
        id INTEGER PRIMARY KEY, snapshot_id INTEGER NOT NULL, question TEXT NOT NULL,
        probability REAL NOT NULL CHECK(probability >= 0 AND probability <= 1),
        rationale TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unapproved',
        reviewed_by TEXT, reviewed_at TEXT, review_notes TEXT,
        UNIQUE(snapshot_id, question), FOREIGN KEY(snapshot_id) REFERENCES report_snapshots(id))''',
):
    c.execute(statement)
conn.commit()

conn.close()
