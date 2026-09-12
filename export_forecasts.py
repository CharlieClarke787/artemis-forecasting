import sqlite3
import csv
from datetime import datetime

def export_to_csv(db_path='forecasts.db', output_path='forecasts_export.csv'):
    conn = sqlite3.connect(db_path)
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
    try:
        c.execute('''
        SELECT d.question, 'Artemis report generator' AS forecaster, d.probability, d.rationale, s.retrieved_at,
               d.status, s.report_title, s.source_url, s.report_date,
               s.content_hash, s.generator_version, s.retrieved_at, s.assumptions
        FROM draft_forecasts d JOIN report_snapshots s ON s.id = d.snapshot_id
        ORDER BY d.id DESC
        ''')
        drafts = c.fetchall()
    except sqlite3.OperationalError:
        drafts = []
    conn.close()
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Question ID', 'Question', 'Forecaster', 'Probability', 'Rationale', 'Forecast Date', 'Outcome', 'Resolution Date', 'Status', 'Report Title', 'Source URL', 'Report Date', 'Content Hash', 'Generator Version', 'Retrieved At', 'Assumptions'])
        
        for row in forecasts:
            qid, question, forecaster, prob, rationale, created_at, outcome, resolved_at = row
            outcome_text = 'YES' if outcome == 1 else ('NO' if outcome == 0 else 'PENDING')
            writer.writerow([qid, question, forecaster, f'{prob:.2%}', rationale or '', created_at[:10], outcome_text, resolved_at[:10] if resolved_at else ''])
        for index, row in enumerate(drafts, 1):
            question, forecaster, prob, rationale, created_at, status, title, source_url, report_date, content_hash, version, retrieved_at, assumptions = row
            writer.writerow([f'DRAFT-{index}', question, forecaster, f'{prob:.2%}', rationale, created_at[:10] if created_at else '', 'NOT SCORED', '', status.upper(), title or '', source_url, report_date or '', content_hash, version, retrieved_at, assumptions])
    
    print(f"SUCCESS! Created '{output_path}'")
    print(f"Total forecasts exported: {len(forecasts)}")

if __name__ == '__main__':
    export_to_csv()
