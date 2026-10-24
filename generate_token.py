import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

def generate_token():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print("config.json not found.")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    gp_config = config.get('google_photos', {})
    credentials_file = gp_config.get('client_secrets_file', 'client_secret.json')

    if not os.path.exists(credentials_file):
        print(f"Credentials file '{credentials_file}' not found in project directory.")
        return

    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    
    print("Initializing Google Photos OAuth Flow...")
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

    auth_url, _ = flow.authorization_url(prompt='consent')

    print("\n" + "="*80)
    print("Please open this link on ANY device with a modern web browser:")
    print("\n" + auth_url + "\n")
    print("="*80 + "\n")

    code = input("Enter the authorization code from that page: ").strip()

    flow.fetch_token(code=code)
    creds = flow.credentials

    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print("\nSuccess! 'token.json' has been generated. You can now run ./run.sh")

if __name__ == '__main__':
    generate_token()
