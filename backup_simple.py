import shutil
import os
from datetime import datetime

def backup_local():
    '''Create a backup zip file'''
    
    try:
        # Create timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_name = f'forecasts_backup_{timestamp}'
        
        # Files to backup
        files = ['forecasts.db', 'add_forecast.py', 'view_dashboard.py', 
                 'resolve_forecast.py', 'export_forecasts.py', 'calibration_chart.py']
        
        # Create zip
        shutil.make_archive(backup_name, 'zip')
        
        print(f"SUCCESS! Created backup: {backup_name}.zip")
        print("You can now upload this to Google Drive manually!")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    backup_local()
    input("Press Enter to close...")
