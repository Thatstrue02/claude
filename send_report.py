#!/usr/bin/env python3
"""
Gmail OAuth2 Auth & Send Script
Nutze dieses Skript nach der OAuth-Autorisierung, um den Bericht zu versenden.

Aufruf:
  python3 send_report.py --code "AUTH_CODE_AUS_DER_URL"
oder wenn bereits autorisiert:
  python3 send_report.py --send
"""

import sys, os, json, base64, argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CLIENT_ID     = os.environ.get("GMAIL_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GMAIL_CLIENT_SECRET", "")
REDIRECT_URI  = "http://localhost:3000/oauth2callback"
CREDS_FILE    = os.path.expanduser("~/.gmail-mcp/credentials.json")
REPORT_FILE   = os.path.join(os.path.dirname(__file__), "husdt_report_2026-04-27.html")
RECIPIENT     = "raemanuel@pm.me"

def exchange_code(code):
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    resp = json.loads(urllib.request.urlopen(req).read())
    os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
    with open(CREDS_FILE, "w") as f:
        json.dump(resp, f)
    print(f"✅ Tokens gespeichert: {CREDS_FILE}")
    return resp

def get_access_token():
    import urllib.request, urllib.parse
    with open(CREDS_FILE) as f:
        creds = json.load(f)
    if "access_token" not in creds:
        raise Exception("Kein Access Token. Bitte zuerst --code verwenden.")
    # Refresh if needed
    if "refresh_token" in creds:
        data = urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token"
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
        new = json.loads(urllib.request.urlopen(req).read())
        creds.update(new)
        with open(CREDS_FILE, "w") as f:
            json.dump(creds, f)
    return creds["access_token"]

def send_email(access_token):
    import urllib.request
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        html_body = f.read()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 HUSDT/Humanity Protocol – Investoren-Report | 27. April 2026"
    msg["From"]    = "me"
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText("Bitte HTML-Version anzeigen.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = json.dumps({"raw": raw}).encode()

    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    print(f"✅ E-Mail gesendet! Message-ID: {resp.get('id')}")
    return resp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", help="OAuth2-Code aus der Redirect-URL")
    parser.add_argument("--send", action="store_true", help="Bericht senden (nach Autorisierung)")
    args = parser.parse_args()

    if args.code:
        print("🔑 Tausche Code gegen Tokens...")
        creds = exchange_code(args.code.strip())
        print("📧 Sende Bericht...")
        token = get_access_token()
        send_email(token)
    elif args.send:
        print("📧 Sende Bericht...")
        token = get_access_token()
        send_email(token)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
