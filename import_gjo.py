import sqlite3
from datetime import datetime

def import_gjo_questions():
    """Import Good Judgment Open questions into the database"""
    
    gjo_questions = [
        "What will be the value of the S&P Global US Manufacturing PMI for December 2026?",
        "What will be the value of the S&P Global France Manufacturing PMI for December 2026?",
        "Will the United States publicly announce or acknowledge that it has executed a military strike within the territory, airspace, or territorial waters of Iran before 24 October 2026?",
        "What will be the average monthly change in US total nonfarm private payrolls in the fourth quarter of 2026, according to ADP?",
        "What will be the spread between US high-yield corporate bonds and US Treasuries on 31 December 2026?",
        "What will be the value of the S&P Global Stanbic IBTC Bank Nigeria PMI for December 2026?",
        "What will be the US annual real GDP growth rate for the fourth quarter of 2026?",
        "What will be the yield for US 10-year Treasury securities on 31 December 2026?",
        "What will be the price of bitcoin on 31 December 2026?",
        "What will be the US civilian unemployment rate (U3) for December 2026?",
        "What will be the average US city price of a pound of ground beef in December 2026?",
        "What will be the sales price of a gallon of on-highway diesel in the US for 28 December 2026?",
        "What will be the average price of a pound of coffee in the US in December 2026?",
        "What will be the spot price per barrel for West Texas Intermediate (WTI) crude oil on 31 December 2026?",
        "What will be the value of the S&P Global HSBC India Services PMI for December 2026?",
        "Will the percentage of Americans who say they have occasion to drink alcohol in 2027 be higher than it was in 2026, according to Gallup?",
        "What will be the value of the S&P Global US Services PMI for December 2026?",
        "What will be the value of the S&P Global France Services PMI for December 2026?",
        "What will be the closing value of the S&P 500 Index on 31 December 2026?",
        "What will be the value of the S&P Global Germany Manufacturing PMI for December 2026?",
        "What will be the value of the S&P Global Germany Services PMI for December 2026?",
        "What will be the value of the S&P Global HSBC India Manufacturing PMI for December 2026?",
        "What will be the value of the S&P Global Qatar PMI (non-energy private sector) for December 2026?",
        "What will be the value of the S&P Global Indonesia Manufacturing PMI for December 2026?",
        "Will Parti Québécois win a majority of National Assembly of Quebec (Assemblée nationale du Québec) seats in the 2026 Quebec general election?",
        "What will be NVIDIA's total revenue in the third quarter of its fiscal year 2027 (approximately August 2026 through October 2026)?",
        "What will be the weekly average interest rate for 30-year fixed rate mortgages in the US for the week ending 31 December 2026?",
        "What will be the 12-month percentage change in the US Consumer Price Index (CPI) for December 2026?",
        "What will be the closing value of the NASDAQ 100 Index on 31 December 2026?",
        "What will be the closing market capitalization for NVIDIA Corp on 28 August 2026?",
        "In the 2026 North Carolina US Senate election race, will the Democratic nominee be leading the Republican nominee in polling on 4 September 2026, according to RealClearPolitics?",
        "What percentage of the party list vote will the Alternative for Germany (Alternative für Deutschland, or AfD) win in the 2026 Saxony-Anhalt Landtag (state parliament) elections?",
        "Will SpaceX successfully complete an in-orbit fuel transfer between two Starship spacecraft before 1 October 2026?",
        "Between 2 April 2026 and 28 August 2026, will the price of gold outperform the price of silver?",
    ]
    
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    added = 0
    skipped = 0
    
    for question_text in gjo_questions:
        # Check if question already exists
        c.execute('SELECT id FROM questions WHERE text = ?', (question_text,))
        if c.fetchone():
            skipped += 1
            continue
        
        # Add new question
        c.execute('''
            INSERT INTO questions (text, source, created_at)
            VALUES (?, 'Good Judgment Open', ?)
        ''', (question_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        added += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n[OK] GJO Import Complete!")
    print(f"[+] Added: {added} new questions")
    print(f"[+] Already existed: {skipped} questions")
    print(f"\nQuick forecast on these questions:")
    print("   python quick_forecast_gjo.py")
    print("\nOr manually add forecasts:")
    print("   python add_forecast.py")

if __name__ == '__main__':
    import_gjo_questions()
