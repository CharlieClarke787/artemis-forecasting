import sqlite3
from datetime import datetime

def resolve_forecast():
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Show all unresolved questions
    c.execute('''
    SELECT q.id, q.text
    FROM questions q
    LEFT JOIN ground_truth gt ON q.id = gt.question_id
    WHERE gt.id IS NULL
    ''')
    
    unresolved = c.fetchall()
    
    if not unresolved:
        print("No unresolved forecasts!")
        return
    
    print("\n=== UNRESOLVED FORECASTS ===\n")
    for qid, text in unresolved:
        print(f"ID {qid}: {text}")
    
    question_id = int(input("\nEnter question ID to resolve: "))
    outcome = int(input("Did it happen? (1 for YES, 0 for NO): "))
    
    # Add ground truth
    c.execute('INSERT INTO ground_truth (question_id, outcome, resolved_at) VALUES (?, ?, ?)',
              (question_id, outcome, datetime.now().isoformat()))
    conn.commit()
    
    # Calculate Brier score for this question
    c.execute('''
    SELECT f.probability FROM forecasts f WHERE f.question_id = ?
    ''', (question_id,))
    
    forecasts = c.fetchall()
    
    if forecasts:
        brier_scores = []
        for (prob,) in forecasts:
            brier = (prob - outcome) ** 2
            brier_scores.append(brier)
            print(f"\n✓ Forecast resolved!")
            print(f"  Predicted: {prob * 100:.0f}%")
            print(f"  Outcome: {'YES' if outcome == 1 else 'NO'}")
            print(f"  Brier Score: {brier:.4f} (lower is better)")
    
    conn.close()

if __name__ == '__main__':
    resolve_forecast()
