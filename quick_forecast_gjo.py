import sqlite3
from datetime import datetime

def quick_forecast_gjo():
    """Quick forecasting interface for GJO questions"""
    
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Get all GJO questions without forecasts yet
    c.execute('''
    SELECT q.id, q.text
    FROM questions q
    WHERE q.source = 'Good Judgment Open'
    AND q.id NOT IN (SELECT question_id FROM forecasts)
    ORDER BY q.id
    ''')
    
    unforecasted = c.fetchall()
    
    if not unforecasted:
        print("\nAll GJO questions have been forecasted already!")
        print("Run: python add_forecast.py to add more forecasts or update existing ones.")
        conn.close()
        return
    
    print(f"\n[GJO Quick Forecast Tool]")
    print(f"Found {len(unforecasted)} unforecasted questions from Good Judgment Open\n")
    
    forecaster_name = input("Your name: ").strip()
    if not forecaster_name:
        forecaster_name = "Forecaster"
    
    count = 0
    for q_id, question_text in unforecasted:
        print(f"\n[{count + 1}/{len(unforecasted)}] {question_text}")
        
        try:
            prob_input = input("Probability 0-100 (or skip): ").strip()
            if prob_input.lower() in ['skip', 's', '']:
                print("  > Skipped")
                continue
            
            prob = float(prob_input) / 100.0
            if prob < 0 or prob > 1:
                print("  > Invalid probability, skipped")
                continue
            
            rationale = input("Brief rationale (optional): ").strip()
            
            # Add forecast
            c.execute('''
                INSERT INTO forecasts (question_id, forecaster, probability, rationale, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (q_id, forecaster_name, prob, rationale, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            print(f"  > Added forecast: {prob*100:.0f}%")
            count += 1
        
        except ValueError:
            print("  > Invalid input, skipped")
    
    conn.close()
    
    print(f"\n[+] Added {count} new forecasts")
    print("\nView your forecasts:")
    print("   python launcher.py")

if __name__ == '__main__':
    quick_forecast_gjo()
    input("\nPress Enter to close...")
