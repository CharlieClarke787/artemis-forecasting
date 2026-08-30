from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import shutil

def backup_to_gdrive():
    '''Backup forecasts.db to Google Drive'''
    
    try:
        # Rename credentials to what pydrive expects
        if os.path.exists('credentials.json') and not os.path.exists('client_secrets.json'):
            shutil.copy('credentials.json', 'client_secrets.json')
        
        print("Authenticating with Google Drive...")
        
        # Authenticate
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)
        
        print("Connected! Uploading backup...")
        
        # Upload database file
        file_name = 'forecasts.db'
        gfile = drive.CreateFile({'title': file_name})
        gfile.SetContentFile(file_name)
        gfile.Upload()
        
        print(f"SUCCESS! Backed up '{file_name}' to Google Drive")
        print(f"File ID: {gfile['id']}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    backup_to_gdrive()
    input("Press Enter to close...")
