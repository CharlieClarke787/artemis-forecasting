import sqlite3
from datetime import datetime

def add_sample_gjo_data():
    """Add sample GJO consensus data for demonstration"""
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Ensure consensus table exists
    c.execute('''
    CREATE TABLE IF NOT EXISTS gjo_consensus (
        id INTEGER PRIMARY KEY,
        question_id INTEGER,
        community_probability REAL,
        expert_probability REAL,
        median_probability REAL,
        updated_at TEXT,
        FOREIGN KEY(question_id) REFERENCES questions(id)
    )
    ''')
    
    # Add sample consensus data for first few GJO questions
    sample_data = [
        (6, 0.55),   # S&P US Manufacturing PMI
        (7, 0.50),   # S&P France Manufacturing PMI
        (8, 0.35),   # Iran military strike
        (9, 0.45),   # US nonfarm payrolls
        (10, 0.60),  # High-yield bond spread
        (11, 0.48),  # Nigeria PMI
        (12, 0.52),  # US GDP growth
        (13, 0.58),  # US Treasury yield
        (14, 0.65),  # Bitcoin price
        (15, 0.42),  # US unemployment
    ]
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    added = 0
    for q_id, median_prob in sample_data:
        c.execute('SELECT id FROM gjo_consensus WHERE question_id = ?', (q_id,))
        if not c.fetchone():
            c.execute('''
                INSERT INTO gjo_consensus (question_id, median_probability, updated_at)
                VALUES (?, ?, ?)
            ''', (q_id, median_prob, now))
            added += 1
    
    conn.commit()
    conn.close()
    
    print(f"[+] Added {added} sample GJO consensus forecasts")
    print("\nNow run:")
    print("   python view_dashboard.py")

if __name__ == '__main__':
    add_sample_gjo_data()
