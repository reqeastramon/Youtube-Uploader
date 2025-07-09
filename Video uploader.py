import os
import webbrowser
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools

# Constants
CLIENT_SECRET_FILE = 'client_secrets.json'
CREDENTIALS_FILE = 'youtube_credentials.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Local server settings for redirect URI
PORT = 8080
REDIRECT_URI = f'http://localhost:{PORT}/'

# A simple handler to capture the OAuth redirect
class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    auth_code = None
    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if 'code' in params:
            OAuthHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication Successful</h1><p>You may now close this window.</p></body></html>")
        else:
            self.send_error(400, "Authorization code not found.")

def start_local_server():
    handler = OAuthHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Waiting for OAuth response on http://localhost:{PORT}/")
        httpd.handle_request()  # handle only one request

def authenticate_youtube_gui():
    # Step 1: Load credentials storage
    storage = Storage(CREDENTIALS_FILE)
    credentials = storage.get()

    if credentials is not None and not credentials.invalid:
        print("✅ Already authenticated.")
        return credentials

    # Step 2: Load client secrets and generate auth URL
    flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=SCOPES, redirect_uri=REDIRECT_URI)
    auth_uri = flow.step1_get_authorize_url()
    
    # Step 3: Open browser to start auth
    print("🔐 Opening browser for authentication...")
    webbrowser.open(auth_uri)

    # Step 4: Start local server to capture the auth code
    server_thread = threading.Thread(target=start_local_server)
    server_thread.start()
    server_thread.join()

    # Step 5: Exchange code for token
    if OAuthHandler.auth_code:
        print("🔁 Exchanging code for credentials...")
        credentials = flow.step2_exchange(OAuthHandler.auth_code)
        storage.put(credentials)
        print("✅ Authentication successful. Token saved to:", CREDENTIALS_FILE)
    else:
        print("❌ Authentication failed. No code received.")

    return credentials

if __name__ == "__main__":
    print("🎮 YouTube OAuth GUI Authenticator")
    authenticate_youtube_gui()
