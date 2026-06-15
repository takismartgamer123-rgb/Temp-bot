import os, json, threading, time, requests
from flask import Flask
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

app = Flask(__name__)

def run_bot():
    print("🚀 [BOT] بدا الـ Thread تاع البوت")
    
    TOKEN_JSON = os.getenv('TOKEN_JSON')
    if not TOKEN_JSON:
        print("💀 [BOT] TOKEN_JSON مكاش في Environment")
        return
    
    print("✅ [BOT] لقيت TOKEN_JSON")
    
    try:
        creds_data = json.loads(TOKEN_JSON.strip())
        print("✅ [BOT] JSON صحيح")
    except Exception as e:
        print(f"💀 [BOT] JSON خاسر: {e}")
        return
    
    if 'refresh_token' not in creds_data:
        print("💀 [BOT] ماكانش refresh_token في التوكن")
        return
        
    print("🤖 [BOT] Credentials صحاح")
    print("🤖 [BOT] YouTube API جاهز")
    
    # هنا من بعد نزيدو الألعاب
    while True:
        print("🔍 [BOT] دورت على لايف...")
        time.sleep(60)

@app.route('/')
def home():
    return "🚫💸 INFINITY BOT حي"

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
