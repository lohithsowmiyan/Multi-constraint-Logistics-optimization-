from pydrive.auth import GoogleAuth 
from pydrive.drive import GoogleDrive
gauth = GoogleAuth() 
drive = GoogleDrive()
gauth.LoadCredentialsFile("goog_creds.txt")
gauth.LoadCredentialsFile("goog_creds.txt") 
if gauth.credentials is None:
        gauth.LocalWebserverAuth() 
elif gauth.access_token_expired: 
        gauth.Refresh() 
else: # Initialize the saved creds 
    gauth.Authorize()
gauth.SaveCredentialsFile("goog_creds.txt")
src_file = drive.CreateFile({'title': 'model data-2.xlsx'}) 
src_file.SetContentFile('model data-2.xlsx')
src_file.Upload({'convert': True})
