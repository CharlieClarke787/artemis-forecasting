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

conn.close()
