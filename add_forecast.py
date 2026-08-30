import sqlite3
from datetime import datetime

def add_forecast():
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    print("\n=== ADD A SANCTIONS FORECAST ===\n")
    
    # Get input from user
    question = input("What is your forecast question? (e.g., 'Will the US sanction Russia by 2025-12-31?'): ")
    forecaster = input("Who is forecasting? (e.g., 'Model A' or 'John Smith'): ")
    probability = float(input("Probability (0 to 1, e.g., 0.75 for 75%): "))
    rationale = input("Why do you forecast this? (optional): ")
    
    # Add question to database
    c.execute('INSERT INTO questions (text, type, created_at) VALUES (?, ?, ?)',
              (question, 'binary', datetime.now().isoformat()))
    conn.commit()
    
    question_id = c.lastrowid
    
    # Add forecast to database
    c.execute('INSERT INTO forecasts (question_id, forecaster, probability, rationale, created_at) VALUES (?, ?, ?, ?, ?)',
              (question_id, forecaster, probability, rationale, datetime.now().isoformat()))
    conn.commit()
    
    print(f"\n✓ Forecast added! (Question ID: {question_id})")
    conn.close()

if __name__ == '__main__':
    add_forecast()
