import sqlite3
from datetime import datetime
import json
import sys
import os

# Add the current directory to path for analytics import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from analytics import calculate_analytics
except ImportError:
    # Fallback if analytics not available
    def calculate_analytics():
        return {
            'total': 0, 'pending': 0, 'resolved': 0,
            'win_rate': 0, 'avg_brier': 0,
            'calibration': [], 'forecasters': []
        }

def view_forecasts():
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Get all forecasts with proper null handling for pending
    c.execute('''
    SELECT 
        q.id,
        q.text,
        f.forecaster,
        f.probability,
        f.rationale,
        f.created_at,
        COALESCE(gt.outcome, -1) as outcome
    FROM questions q
    JOIN forecasts f ON q.id = f.question_id
    LEFT JOIN ground_truth gt ON q.id = gt.question_id
    ORDER BY CASE WHEN gt.outcome IS NULL THEN 0 ELSE 1 END ASC, f.created_at DESC
    ''')
    
    forecasts = c.fetchall()
    conn.close()
    
    # Get analytics
    analytics = calculate_analytics()
    
    # Create HTML file with Artemis branding
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artemis Forecasting - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', sans-serif;
            background: #f8f7f5;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 2px solid #2d5016;
        }
        .header-left h1 {
            font-family: 'Playfair Display', serif;
            font-size: 48px;
            color: #2d5016;
            margin-bottom: 5px;
            font-weight: 700;
        }
        .header-left p {
            font-size: 14px;
            color: #6b4423;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .logo { width: 60px; height: 60px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 50px;
        }
        .stat-box {
            background: white;
            padding: 25px;
            border-left: 4px solid #2d5016;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .stat-number { 
            font-size: 36px; 
            font-weight: 700; 
            color: #2d5016;
            margin-bottom: 8px;
        }
        .stat-label { 
            font-size: 13px; 
            color: #6b4423;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .section-title {
            font-family: 'Playfair Display', serif;
            font-size: 28px;
            color: #2d5016;
            margin: 40px 0 25px 0;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0d5cc;
        }
        .forecast {
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 5px solid #6b4423;
            transition: box-shadow 0.2s;
        }
        .forecast:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
        .forecast.pending { border-left-color: #d4a574; }
        .forecast.resolved { border-left-color: #2d5016; }
        .question {
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            font-size: 20px;
            color: #2d5016;
            margin-bottom: 20px;
            line-height: 1.4;
        }
        .probability-row {
            display: flex;
            align-items: center;
            gap: 20px;
            margin: 20px 0;
        }
        .probability-bar {
            flex: 1;
            height: 10px;
            background: #e0d5cc;
            border-radius: 5px;
            overflow: hidden;
        }
        .probability-fill { 
            height: 100%; 
            border-radius: 5px; 
            transition: width 0.3s;
        }
        .probability-fill.high { background: #2d5016; }
        .probability-fill.medium { background: #6b4423; }
        .probability-fill.low { background: #d4a574; }
        .probability-text {
            font-size: 28px;
            font-weight: 700;
            min-width: 80px;
            text-align: right;
            color: #2d5016;
        }
        .meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0d5cc;
            font-size: 13px;
            color: #666;
        }
        .meta-label { 
            font-weight: 600; 
            color: #6b4423; 
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }
        .meta-value { margin-top: 5px; color: #333; }
        .status {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status.resolved { 
            background: #d4edda; 
            color: #2d5016;
        }
        .status.pending { 
            background: #fff9e6;
            color: #6b4423;
        }
        .rationale { 
            font-style: italic; 
            color: #555; 
            margin-top: 15px;
            padding: 15px;
            background: #faf8f5;
            border-left: 3px solid #6b4423;
            border-radius: 2px;
            font-size: 14px;
        }
        .empty { 
            text-align: center; 
            color: #6b4423; 
            padding: 60px 40px;
            font-size: 18px;
            background: white;
        }
        .leaderboard {
            background: white;
            border-radius: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
            margin-bottom: 40px;
        }
        .leaderboard-row {
            display: grid;
            grid-template-columns: 50px 1fr repeat(3, 120px);
            gap: 20px;
            padding: 20px 30px;
            align-items: center;
            border-bottom: 1px solid #e0d5cc;
            transition: background 0.2s;
        }
        .leaderboard-row:hover { background: #faf8f5; }
        .leaderboard-row:last-child { border-bottom: none; }
        .rank {
            font-family: 'Playfair Display', serif;
            font-size: 20px;
            font-weight: 700;
            color: #2d5016;
            text-align: center;
        }
        .forecaster-name {
            font-weight: 600;
            color: #333;
        }
        .metric {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        .metric-label {
            font-size: 11px;
            color: #6b4423;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        .metric-value {
            font-size: 16px;
            font-weight: 700;
            color: #333;
            margin-top: 3px;
        }
        .chart-container {
            background: white;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .chart-container canvas {
            max-height: 400px;
        }
        .comparison-table {
            background: white;
            border-radius: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
            margin-bottom: 40px;
        }
        .comparison-row {
            display: grid;
            grid-template-columns: 2fr 100px 100px 100px 100px 80px;
            gap: 15px;
            padding: 20px;
            align-items: center;
            border-bottom: 1px solid #e0d5cc;
            font-size: 13px;
        }
        .comparison-row:hover { background: #faf8f5; }
        .comparison-row:last-child { border-bottom: none; }
        .comparison-row.header {
            background: #f5f2ed;
            font-weight: 600;
            color: #6b4423;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            padding: 15px 20px;
        }
        .comparison-row.header:hover { background: #f5f2ed; }
        .comparison-q { font-weight: 500; color: #333; }
        .comparison-num { text-align: center; font-weight: 600; }
        .comparison-win { text-align: center; color: #2d5016; font-weight: 600; }
        .comparison-loss { text-align: center; color: #d4a574; }
        .gjo-summary {
            background: white;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
        }
        .gjo-metric {
            text-align: center;
        }
        .gjo-metric-label {
            font-size: 12px;
            color: #6b4423;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .gjo-metric-value {
            font-size: 32px;
            font-weight: 700;
            color: #2d5016;
        }
        .gjo-metric-sub {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        @media (max-width: 600px) {
            .header { flex-direction: column; text-align: center; gap: 20px; }
            .stats { grid-template-columns: 1fr; }
            .meta { grid-template-columns: 1fr; }
            .header-left h1 { font-size: 36px; }
            .comparison-row { grid-template-columns: 1fr; }
            .gjo-summary { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>ARTEMIS FORECASTING</h1>
                <p>Dashboard & Analytics</p>
            </div>
            <svg class="logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="48" fill="none" stroke="#2d5016" stroke-width="2"/>
                <ellipse cx="40" cy="35" rx="8" ry="12" fill="#2d5016"/>
                <ellipse cx="60" cy="35" rx="8" ry="12" fill="#2d5016"/>
                <circle cx="38" cy="32" r="3" fill="#f8f7f5"/>
                <circle cx="62" cy="32" r="3" fill="#f8f7f5"/>
                <path d="M 35 50 Q 40 60 50 58 Q 60 60 65 50" stroke="#6b4423" stroke-width="2" fill="none" stroke-linecap="round"/>
                <path d="M 30 45 L 25 55 Q 27 58 30 57" stroke="#6b4423" stroke-width="1.5" fill="none"/>
                <path d="M 70 45 L 75 55 Q 73 58 70 57" stroke="#6b4423" stroke-width="1.5" fill="none"/>
            </svg>
        </div>
'''
    
    if forecasts:
        # Calculate stats
        total = len(forecasts)
        resolved = sum(1 for f in forecasts if f[6] != -1)
        pending = total - resolved
        
        html += f'''
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{analytics['total']}</div>
                <div class="stat-label">Total Forecasts</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{analytics['pending']}</div>
                <div class="stat-label">Pending</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{analytics['resolved']}</div>
                <div class="stat-label">Resolved</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-box performance">
                <div class="stat-number" style="color: #2d5016;">{analytics['win_rate']:.1f}%</div>
                <div class="stat-label">Win Rate</div>
            </div>
            <div class="stat-box performance">
                <div class="stat-number" style="color: #2d5016;">{analytics['avg_brier']:.3f}</div>
                <div class="stat-label">Brier Score</div>
            </div>
            <div class="stat-box performance">
                <div class="stat-number" style="color: #2d5016;">{len(analytics['forecasters'])}</div>
                <div class="stat-label">Forecasters</div>
            </div>
        </div>
'''
        
        # Group forecasts into pending and resolved
        pending_forecasts = [f for f in forecasts if f[6] == -1]
        resolved_forecasts = [f for f in forecasts if f[6] != -1]
        
        # Add forecaster leaderboard
        if analytics['forecasters']:
            html += '<h2 class="section-title">Forecaster Performance</h2>'
            html += '<div class="leaderboard">'
            for i, forecaster in enumerate(analytics['forecasters'][:10], 1):
                html += f'''
        <div class="leaderboard-row">
            <div class="rank">#{i}</div>
            <div class="forecaster-name">{forecaster['name']}</div>
            <div class="metric">
                <span class="metric-label">Resolved</span>
                <span class="metric-value">{forecaster['resolved']}/{forecaster['total']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Win Rate</span>
                <span class="metric-value" style="color: #2d5016;">{forecaster['win_rate']}%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Brier</span>
                <span class="metric-value">{forecaster['brier_score']}</span>
            </div>
        </div>
'''
            html += '</div>'
        
        # Add GJO comparison section
        if analytics.get('gjo_comparison') and analytics['gjo_comparison']['questions']:
            gjo_comp = analytics['gjo_comparison']
            your_wins = gjo_comp['better_than_consensus']
            total_compared = len(gjo_comp['questions'])
            
            html += f'''
        <h2 class="section-title">Good Judgment Open - vs Community</h2>
        <div class="gjo-summary">
            <div class="gjo-metric">
                <div class="gjo-metric-label">Your Brier Score</div>
                <div class="gjo-metric-value">{gjo_comp['your_brier']}</div>
                <div class="gjo-metric-sub">Lower is better</div>
            </div>
            <div class="gjo-metric">
                <div class="gjo-metric-label">Community Brier</div>
                <div class="gjo-metric-value">{gjo_comp['consensus_brier']}</div>
                <div class="gjo-metric-sub">{total_compared} forecasts</div>
            </div>
            <div class="gjo-metric">
                <div class="gjo-metric-label">Beat Community</div>
                <div class="gjo-metric-value" style="color: #2d5016;">{your_wins}/{total_compared}</div>
                <div class="gjo-metric-sub">{round(your_wins/total_compared*100, 0):.0f}% better</div>
            </div>
        </div>
        <div class="comparison-table">
            <div class="comparison-row header">
                <div>Question</div>
                <div>Your %</div>
                <div>Community %</div>
                <div>Outcome</div>
                <div>Your Brier</div>
                <div>Result</div>
            </div>
'''
            for q_data in gjo_comp['questions']:
                result_class = 'comparison-win' if q_data['beat_consensus'] else 'comparison-loss'
                result_text = 'Won' if q_data['beat_consensus'] else 'Lost'
                outcome_text = 'YES' if q_data['outcome'] == 1 else 'NO'
                
                html += f'''
            <div class="comparison-row">
                <div class="comparison-q">{q_data['question']}</div>
                <div class="comparison-num">{q_data['your_prob']:.0f}%</div>
                <div class="comparison-num">{q_data['consensus_prob']:.0f}%</div>
                <div class="comparison-num">{outcome_text}</div>
                <div class="comparison-num">{q_data['your_brier']}</div>
                <div class="{result_class}">{result_text}</div>
            </div>
'''
            html += '</div>'
        
        # Add calibration chart
        if analytics['calibration']:
            calibration_json = json.dumps(analytics['calibration'])
            html += f'''
        <h2 class="section-title">Calibration Analysis</h2>
        <div class="chart-container">
            <canvas id="calibrationChart"></canvas>
        </div>
        <script>
            const calibrationData = {calibration_json};
            const bins = calibrationData.map(d => d.bin);
            const predicted = calibrationData.map(d => d.predicted);
            const actual = calibrationData.map(d => d.actual);
            
            const ctx = document.getElementById('calibrationChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: bins,
                    datasets: [
                        {{
                            label: 'Predicted Probability',
                            data: predicted,
                            borderColor: '#2d5016',
                            backgroundColor: 'rgba(45, 80, 22, 0.05)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 6,
                            pointBackgroundColor: '#2d5016',
                            pointBorderWidth: 0
                        }},
                        {{
                            label: 'Actual Resolution Rate',
                            data: actual,
                            borderColor: '#6b4423',
                            backgroundColor: 'rgba(107, 68, 35, 0.05)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 6,
                            pointBackgroundColor: '#6b4423',
                            pointBorderWidth: 0
                        }},
                        {{
                            label: 'Perfect Calibration',
                            data: bins.map((_, i) => (i * 10 + 5)),
                            borderColor: '#ddd',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0,
                            tension: 0
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                            labels: {{
                                font: {{ family: "'Inter', sans-serif", size: 12 }},
                                color: '#333',
                                usePointStyle: true,
                                padding: 20
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            ticks: {{
                                callback: function(value) {{ return value + '%'; }},
                                font: {{ size: 11 }},
                                color: '#999'
                            }},
                            grid: {{ color: 'rgba(0,0,0,0.05)' }}
                        }},
                        x: {{
                            ticks: {{
                                font: {{ size: 11 }},
                                color: '#999'
                            }},
                            grid: {{ display: false }}
                        }}
                    }}
                }}
            }});
        </script>
        '''
        
        # Show pending forecasts
        if pending_forecasts:
            html += '<h2 class="section-title">Active Forecasts</h2>'
            for forecast_id, question, forecaster, prob, rationale, created_at, outcome in pending_forecasts:
                # Color based on probability
                if prob >= 0.7:
                    color_class = 'high'
                    color_hex = '#2d5016'
                elif prob >= 0.5:
                    color_class = 'medium'
                    color_hex = '#6b4423'
                else:
                    color_class = 'low'
                    color_hex = '#d4a574'
                
                html += f'''
        <div class="forecast pending">
            <div class="question">{question}</div>
            <div class="probability-row">
                <div class="probability-bar">
                    <div class="probability-fill {color_class}" style="width: {prob * 100}%;"></div>
                </div>
                <div class="probability-text" style="color: {color_hex};">{prob * 100:.0f}%</div>
            </div>
            <div class="meta">
                <div>
                    <div class="meta-label">Forecaster</div>
                    <div class="meta-value">{forecaster}</div>
                </div>
                <div>
                    <div class="meta-label">Date Added</div>
                    <div class="meta-value">{created_at[:10]}</div>
                </div>
            </div>
'''
                if rationale:
                    html += f'<div class="rationale">Reasoning: {rationale}</div>'
                
                html += '<span class="status pending">Pending</span></div>'
        
        # Show resolved forecasts
        if resolved_forecasts:
            html += '<h2 class="section-title">Resolved Forecasts</h2>'
            for forecast_id, question, forecaster, prob, rationale, created_at, outcome in resolved_forecasts:
                # Color based on probability
                if prob >= 0.7:
                    color_class = 'high'
                    color_hex = '#2d5016'
                elif prob >= 0.5:
                    color_class = 'medium'
                    color_hex = '#6b4423'
                else:
                    color_class = 'low'
                    color_hex = '#d4a574'
                
                html += f'''
        <div class="forecast resolved">
            <div class="question">{question}</div>
            <div class="probability-row">
                <div class="probability-bar">
                    <div class="probability-fill {color_class}" style="width: {prob * 100}%;"></div>
                </div>
                <div class="probability-text" style="color: {color_hex};">{prob * 100:.0f}%</div>
            </div>
            <div class="meta">
                <div>
                    <div class="meta-label">Forecaster</div>
                    <div class="meta-value">{forecaster}</div>
                </div>
                <div>
                    <div class="meta-label">Resolved</div>
                    <div class="meta-value">{"YES" if outcome == 1 else "NO"}</div>
                </div>
            </div>
'''
                if rationale:
                    html += f'<div class="rationale">Reasoning: {rationale}</div>'
                
                html += f'<span class="status resolved">Resolved: {"YES" if outcome == 1 else "NO"}</span></div>'
    else:
        html += '<div class="empty">No forecasts yet. Run: python add_forecast.py</div>'
    
    html += '''
    </div>
</body>
</html>'''
    
    # Save HTML file with UTF-8 encoding
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Dashboard updated! Opening in browser...")
    import webbrowser
    webbrowser.open('dashboard.html')

if __name__ == '__main__':
    view_forecasts()
