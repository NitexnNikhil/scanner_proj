import os
import qrcode
import hashlib
from getpass import getpass
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === SETTINGS ===
SCOPES = ['https://www.googleapis.com/auth/drive.file']
MPIN_HASH = 'fe2592b42a727e977f055947385b709cc82b16b9a87f88c6abf3900d65d0cdc3'  # Use hash_mpin('1234') to generate a secure hash

def hash_mpin(mpin):
    return hashlib.sha256(mpin.encode()).hexdigest()

# def auth_google_drive():
#     creds = None
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#         creds = flow.run_local_server(port=0)
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     return build('drive', 'v3', credentials=creds)


def auth_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        auth_url, _ = flow.authorization_url(prompt='consent')

        print("🔐 Visit this URL to authorize the app:")
        print(auth_url)

        code = input("📥 Paste the code here: ")
        flow.fetch_token(code=code)

        creds = flow.credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def upload_file(service, filename, folder_name="SharedDocs"):
    folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    folder_id = folder.get('id')

    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(filename, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    file_id = file.get('id')
    # Make it publicly readable
    permission = {'type': 'anyone', 'role': 'reader'}
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Generate a shareable link
    link = f'https://drive.google.com/file/d/{file_id}/view?usp=sharing'
    return link, file_id

def generate_qr(link):
    img = qrcode.make(link)
    img.save("qr_link.png")
    print("QR code saved as 'qr_link.png'")

def main():
    mpin_input = getpass("Enter your MPIN for edit access: ")
    if hash_mpin(mpin_input) != MPIN_HASH:
        print("\n[⚠] Incorrect MPIN. Uploading document with read-only access only.")
    
    service = auth_google_drive()
    filename = input("Enter the filename to upload: ")
    link, file_id = upload_file(service, filename)
    
    print(f"\n✅ File uploaded. Access it here:\n{link}")
    generate_qr(link)

    if hash_mpin(mpin_input) == MPIN_HASH:
        print("[🔓] Owner authenticated. You can now manage the file through your Drive account.")

if __name__ == '__main__':
    main()
