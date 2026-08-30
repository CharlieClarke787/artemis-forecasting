import sqlite3

def calibration_chart():
    conn = sqlite3.connect('forecasts.db')
    c = conn.cursor()
    
    # Get all resolved forecasts
    c.execute('''
    SELECT f.probability, gt.outcome
    FROM forecasts f
    JOIN ground_truth gt ON f.question_id = gt.question_id
    ''')
    
    resolved = c.fetchall()
    conn.close()
    
    if not resolved:
        print("No resolved forecasts yet!")
        return
    
    # Group into bins
    bins = {i: {'predictions': [], 'outcomes': []} for i in range(10)}
    
    for prob, outcome in resolved:
        bin_idx = min(int(prob * 10), 9)
        bins[bin_idx]['predictions'].append(prob)
        bins[bin_idx]['outcomes'].append(outcome)
    
    # Calculate accuracy per bin
    bin_data = []
    for bin_idx in range(10):
        if bins[bin_idx]['predictions']:
            avg_pred = sum(bins[bin_idx]['predictions']) / len(bins[bin_idx]['predictions'])
            actual = sum(bins[bin_idx]['outcomes']) / len(bins[bin_idx]['outcomes'])
            count = len(bins[bin_idx]['predictions'])
            bin_data.append({
                'bin': f"{bin_idx * 10}-{(bin_idx + 1) * 10}%",
                'predicted': avg_pred,
                'actual': actual,
                'count': count
            })
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>Calibration Chart</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .explanation { color: #666; margin: 20px 0; line-height: 1.6; }
        canvas { max-width: 100%; }
        .bins { margin-top: 30px; }
        .bin { background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; }
        .bin-title { font-weight: bold; font-size: 16px; }
        .bin-stats { color: #666; margin-top: 8px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Calibration Chart</h1>
        <div class="explanation">
            <strong>What this means:</strong> A well-calibrated forecast means when you predict 70%, it should happen about 70% of the time. The blue line shows your predictions, the orange line shows what actually happened.
        </div>
        <canvas id="calibrationChart"></canvas>
        <div class="bins">
            <h2>Details by Probability Bin</h2>
'''
    
    for bin_info in bin_data:
        html += f'''
            <div class="bin">
                <div class="bin-title">{bin_info["bin"]}</div>
                <div class="bin-stats">
                    Average Prediction: {bin_info["predicted"]:.1%} | Actual Outcome: {bin_info["actual"]:.1%} | Forecasts: {bin_info["count"]}
                </div>
            </div>
'''
    
    labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%']
    predicted_data = [b['predicted'] * 100 for b in bin_data]
    actual_data = [b['actual'] * 100 for b in bin_data]
    
    html += f'''
        </div>
        <script>
            const ctx = document.getElementById('calibrationChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [
                        {{
                            label: 'Your Predictions',
                            data: {predicted_data},
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            fill: true
                        }},
                        {{
                            label: 'What Actually Happened',
                            data: {actual_data},
                            borderColor: '#f39c12',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            tension: 0.4,
                            fill: true
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ position: 'top' }} }},
                    scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
                }}
            }});
        </script>
    </body>
</html>'''
    
    with open('calibration_chart.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("SUCCESS! Opening calibration chart...")
    import webbrowser
    webbrowser.open('calibration_chart.html')

if __name__ == '__main__':
    calibration_chart()
