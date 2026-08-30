import sqlite3
import csv
from datetime import datetime

def export_to_csv():
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Get all forecasts with their scores
    c.execute('''
    SELECT 
        q.id,
        q.text,
        f.forecaster,
        f.probability,
        f.rationale,
        f.created_at,
        gt.outcome,
        gt.resolved_at
    FROM questions q
    JOIN forecasts f ON q.id = f.question_id
    LEFT JOIN ground_truth gt ON q.id = gt.question_id
    ORDER BY f.created_at DESC
    ''')
    
    forecasts = c.fetchall()
    conn.close()
    
    # Write to CSV
    with open('forecasts_export.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Question ID', 'Question', 'Forecaster', 'Probability', 'Rationale', 'Forecast Date', 'Outcome', 'Resolution Date'])
        
        for row in forecasts:
            qid, question, forecaster, prob, rationale, created_at, outcome, resolved_at = row
            outcome_text = 'YES' if outcome == 1 else ('NO' if outcome == 0 else 'PENDING')
            writer.writerow([qid, question, forecaster, f'{prob:.2%}', rationale or '', created_at[:10], outcome_text, resolved_at[:10] if resolved_at else ''])
    
    print("SUCCESS! Created 'forecasts_export.csv'")
    print(f"Total forecasts exported: {len(forecasts)}")

if __name__ == '__main__':
    export_to_csv()
