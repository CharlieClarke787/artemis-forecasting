import webbrowser
import os
import sqlite3
from pathlib import Path

def launch_forecasting():
    '''Launch the forecasting app'''
    
    # Get the current directory
    app_dir = Path(__file__).parent
    
    # Check if database exists
    db_path = app_dir / 'forecasts.db'
    if not db_path.exists():
        print("Error: forecasts.db not found!")
        input("Press Enter to exit...")
        return
    
    # Open the index.html in browser
    index_path = app_dir / 'index.html'
    if index_path.exists():
        webbrowser.open(f'file:///{index_path}')
        print("Forecasting app launched!")
    else:
        print("Error: index.html not found!")
        input("Press Enter to exit...")

if __name__ == '__main__':
    launch_forecasting()
