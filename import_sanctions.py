import sqlite3
import json

def import_sample_sanctions():
    '''Import sample OFAC sanctions data into the database'''
    
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Sample real sanctions data (simplified)
    sample_sanctions = [
        {
            'entity': 'Russian Federation',
            'reason': 'Ukraine invasion',
            'date': '2022-02-24',
            'type': 'Country Sanctions',
            'source': 'US Treasury OFAC'
        },
        {
            'entity': 'Iran Central Bank',
            'reason': 'Nuclear program concerns',
            'date': '2013-11-24',
            'type': 'Entity Sanctions',
            'source': 'US Treasury OFAC'
        },
        {
            'entity': 'North Korea',
            'reason': 'Human rights violations',
            'date': '2010-06-16',
            'type': 'Country Sanctions',
            'source': 'US Treasury OFAC'
        },
    ]
    
    # Create sanctions table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS sanctions (
        id INTEGER PRIMARY KEY,
        entity TEXT,
        reason TEXT,
        date TEXT,
        type TEXT,
        source TEXT
    )
    ''')
    
    # Insert sample data
    for sanction in sample_sanctions:
        c.execute('INSERT INTO sanctions (entity, reason, date, type, source) VALUES (?, ?, ?, ?, ?)',
                  (sanction['entity'], sanction['reason'], sanction['date'], sanction['type'], sanction['source']))
    
    conn.commit()
    
    # Show what was imported
    c.execute('SELECT COUNT(*) FROM sanctions')
    count = c.fetchone()[0]
    
    print(f"SUCCESS! Imported {count} sample sanctions")
    print("\nRecent sanctions:")
    
    c.execute('SELECT entity, reason, date FROM sanctions ORDER BY date DESC LIMIT 5')
    for entity, reason, date in c.fetchall():
        print(f"  - {entity} ({date}): {reason}")
    
    conn.close()

if __name__ == '__main__':
    import_sample_sanctions()
