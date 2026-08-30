import sqlite3
from datetime import datetime

def setup_gjo_consensus():
    """Add consensus tracking table for GJO questions"""
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Create table for tracking GJO community consensus
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
    
    conn.commit()
    conn.close()
    print("[+] GJO consensus table created")

def add_consensus(question_id, community_prob=None, expert_prob=None, median_prob=None):
    """Add or update consensus for a question"""
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    c.execute('SELECT id FROM gjo_consensus WHERE question_id = ?', (question_id,))
    existing = c.fetchone()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if existing:
        c.execute('''
            UPDATE gjo_consensus 
            SET community_probability = ?, expert_probability = ?, median_probability = ?, updated_at = ?
            WHERE question_id = ?
        ''', (community_prob, expert_prob, median_prob, now, question_id))
    else:
        c.execute('''
            INSERT INTO gjo_consensus (question_id, community_probability, expert_probability, median_probability, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (question_id, community_prob, expert_prob, median_prob, now))
    
    conn.commit()
    conn.close()

def import_gjo_consensus():
    """Interactive tool to add GJO consensus data from weekly emails"""
    
    setup_gjo_consensus()
    
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Get GJO questions
    c.execute('''
    SELECT q.id, q.text
    FROM questions q
    WHERE q.source = 'Good Judgment Open'
    ORDER BY q.id
    ''')
    
    questions = c.fetchall()
    conn.close()
    
    if not questions:
        print("No GJO questions found. Run: python import_gjo.py")
        return
    
    print(f"\n[GJO Consensus Import Tool]")
    print(f"Add community forecasts from GJO emails\n")
    print("Instructions:")
    print("- Copy median probability from GJO email for each question")
    print("- Press Enter to skip a question")
    print("- Type 'quit' to finish\n")
    
    added = 0
    for q_id, question_text in questions[:10]:  # First 10 for quick input
        print(f"\n[Q{q_id}] {question_text}")
        
        try:
            prob_input = input("GJO Median Probability (0-100, or skip): ").strip()
            
            if prob_input.lower() in ['quit', 'q']:
                break
            
            if prob_input.lower() in ['skip', 's', '']:
                continue
            
            prob = float(prob_input) / 100.0
            if prob < 0 or prob > 1:
                print("  > Invalid probability, skipped")
                continue
            
            add_consensus(q_id, median_prob=prob)
            print(f"  > Added consensus: {prob*100:.0f}%")
            added += 1
        
        except ValueError:
            print("  > Invalid input, skipped")
    
    print(f"\n[+] Added {added} consensus forecasts")
    print("View your performance vs community:")
    print("   python launcher.py")

if __name__ == '__main__':
    import_gjo_consensus()
