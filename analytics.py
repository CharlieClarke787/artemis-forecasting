import sqlite3
from datetime import datetime
import json

def calculate_analytics(db_path='forecasts.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get all forecasts with outcomes
    c.execute('''
    SELECT 
        q.id,
        q.text,
        q.source,
        f.forecaster,
        f.probability,
        f.created_at,
        COALESCE(gt.outcome, -1) as outcome,
        COALESCE(gc.median_probability, NULL) as consensus
    FROM questions q
    JOIN forecasts f ON q.id = f.question_id
    LEFT JOIN ground_truth gt ON q.id = gt.question_id
    LEFT JOIN gjo_consensus gc ON q.id = gc.question_id
    ORDER BY f.created_at DESC
    ''')
    
    all_forecasts = c.fetchall()
    conn.close()
    
    # Calculate metrics
    resolved = [f for f in all_forecasts if f[6] != -1]
    pending = [f for f in all_forecasts if f[6] == -1]
    gjo_questions = [f for f in all_forecasts if f[2] == 'Good Judgment Open']
    gjo_resolved = [f for f in gjo_questions if f[6] != -1]
    
    # Accuracy metrics
    win_rate = 0
    avg_brier = 0
    calibration_bins = {
        '0-10%': {'predictions': [], 'outcomes': []},
        '10-20%': {'predictions': [], 'outcomes': []},
        '20-30%': {'predictions': [], 'outcomes': []},
        '30-40%': {'predictions': [], 'outcomes': []},
        '40-50%': {'predictions': [], 'outcomes': []},
        '50-60%': {'predictions': [], 'outcomes': []},
        '60-70%': {'predictions': [], 'outcomes': []},
        '70-80%': {'predictions': [], 'outcomes': []},
        '80-90%': {'predictions': [], 'outcomes': []},
        '90-100%': {'predictions': [], 'outcomes': []},
    }
    
    if resolved:
        correct = sum(1 for f in resolved if (f[4] >= 0.5 and f[6] == 1) or (f[4] < 0.5 and f[6] == 0))
        win_rate = (correct / len(resolved)) * 100
        
        # Brier score
        brier_scores = []
        for f in resolved:
            bs = (f[4] - f[6]) ** 2
            brier_scores.append(bs)
        avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 0
        
        # Calibration binning
        for f in resolved:
            prob = f[4]
            outcome = f[6]
            
            if prob < 0.1:
                bin_key = '0-10%'
            elif prob < 0.2:
                bin_key = '10-20%'
            elif prob < 0.3:
                bin_key = '20-30%'
            elif prob < 0.4:
                bin_key = '30-40%'
            elif prob < 0.5:
                bin_key = '40-50%'
            elif prob < 0.6:
                bin_key = '50-60%'
            elif prob < 0.7:
                bin_key = '60-70%'
            elif prob < 0.8:
                bin_key = '70-80%'
            elif prob < 0.9:
                bin_key = '80-90%'
            else:
                bin_key = '90-100%'
            
            calibration_bins[bin_key]['predictions'].append(prob)
            calibration_bins[bin_key]['outcomes'].append(outcome)
    
    # Prepare calibration data for chart
    calibration_data = []
    for bin_key in sorted(calibration_bins.keys()):
        bin_data = calibration_bins[bin_key]
        if bin_data['predictions']:
            avg_prob = sum(bin_data['predictions']) / len(bin_data['predictions'])
            actual_rate = sum(bin_data['outcomes']) / len(bin_data['outcomes'])
            calibration_data.append({
                'bin': bin_key,
                'predicted': round(avg_prob * 100, 1),
                'actual': round(actual_rate * 100, 1),
                'count': len(bin_data['predictions'])
            })
    
    # Forecaster performance
    forecaster_stats = {}
    for f in all_forecasts:
        forecaster = f[3]  # f[3] is forecaster name
        if forecaster not in forecaster_stats:
            forecaster_stats[forecaster] = {
                'total': 0,
                'resolved': 0,
                'correct': 0,
                'brier_scores': []
            }
        
        forecaster_stats[forecaster]['total'] += 1
        
        if f[6] != -1:  # resolved
            forecaster_stats[forecaster]['resolved'] += 1
            if (f[4] >= 0.5 and f[6] == 1) or (f[4] < 0.5 and f[6] == 0):
                forecaster_stats[forecaster]['correct'] += 1
            bs = (f[4] - f[6]) ** 2
            forecaster_stats[forecaster]['brier_scores'].append(bs)
    
    # Calculate forecaster metrics
    forecaster_data = []
    for name, stats in forecaster_stats.items():
        if stats['resolved'] > 0:
            win_pct = (stats['correct'] / stats['resolved']) * 100
            avg_brier_score = sum(stats['brier_scores']) / len(stats['brier_scores'])
        else:
            win_pct = 0
            avg_brier_score = 0
        
        forecaster_data.append({
            'name': name,
            'total': stats['total'],
            'resolved': stats['resolved'],
            'correct': stats['correct'],
            'win_rate': round(win_pct, 1),
            'brier_score': round(avg_brier_score, 3)
        })
    
    # GJO comparison analytics
    gjo_comparison = {
        'your_brier': 0,
        'consensus_brier': 0,
        'better_than_consensus': 0,
        'questions': []
    }
    
    if gjo_resolved:
        your_scores = []
        consensus_scores = []
        better = 0
        
        for f in gjo_resolved:
            your_bs = (f[4] - f[6]) ** 2
            your_scores.append(your_bs)
            
            if f[7] is not None:  # consensus exists
                consensus_bs = (f[7] - f[6]) ** 2
                consensus_scores.append(consensus_bs)
                
                # Compare
                if your_bs < consensus_bs:
                    better += 1
                
                gjo_comparison['questions'].append({
                    'question': f[1][:60] + '...' if len(f[1]) > 60 else f[1],
                    'your_prob': round(f[4] * 100, 1),
                    'consensus_prob': round(f[7] * 100, 1),
                    'outcome': f[6],
                    'your_brier': round(your_bs, 3),
                    'consensus_brier': round(consensus_bs, 3),
                    'beat_consensus': your_bs < consensus_bs
                })
        
        if your_scores:
            gjo_comparison['your_brier'] = round(sum(your_scores) / len(your_scores), 3)
        
        if consensus_scores:
            gjo_comparison['consensus_brier'] = round(sum(consensus_scores) / len(consensus_scores), 3)
            gjo_comparison['better_than_consensus'] = better
    
    return {
        'total': len(all_forecasts),
        'pending': len(pending),
        'resolved': len(resolved),
        'win_rate': round(win_rate, 1),
        'avg_brier': round(avg_brier, 3),
        'calibration': calibration_data,
        'forecasters': sorted(forecaster_data, key=lambda x: x['win_rate'], reverse=True),
        'gjo_total': len(gjo_questions),
        'gjo_resolved': len(gjo_resolved),
        'gjo_comparison': gjo_comparison
    }

if __name__ == '__main__':
    analytics = calculate_analytics()
    print(json.dumps(analytics, indent=2))
