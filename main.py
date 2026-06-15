from flask import Flask
import subprocess, threading, os, time, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

@app.route('/')
def home():
    return "INFINITY GEN Bot V2.3 Debug 🚫💸"

def start_stream():
    print("📺 [STREAM] نحاول نطلع البث...")
    stream_key = os.environ.get('YT_STREAM_KEY')
    if not stream_key:
        print("💀 [STREAM] YT_STREAM_KEY فارغ")
        return
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '300k',
           '-s', '854x480', '-c:a', 'aac', '-b:a', '32k', '-f', 'flv', rtmp_url]
    print("📺 [STREAM] البث شغال")
    while True: subprocess.run(cmd); time.sleep(5)

def start_bot():
    print("🤖 [BOT] بداية التشغيل...")
    try:
        token_raw = os.environ.get('TOKEN_JSON')
        if not token_raw:
            print("💀 [BOT] TOKEN_JSON فارغ في Environment")
            return
        print(f"🤖 [BOT] TOKEN_JSON موجود. الطول: {len(token_raw)}")
        
        token_json = json.loads(token_raw)
        print("🤖 [BOT] JSON صحيح")
        
        creds = Credentials.from_authorized_user_info(token_json)
        print("🤖 [BOT] Credentials صحاح")
        
        youtube = build('youtube', 'v3', credentials=creds)
        print("🤖 [BOT] YouTube API جاهز")
        
        ch = youtube.channels().list(part="id", mine=True).execute()
        bot_id = ch['items'][0]['id']
        print(f"✅ [BOT] ID البوت: {bot_id}")
        
        live_chat_id = None
        for status in ["active", "all"]:
            print(f"🔍 [BOT] نحوس في {status}...")
            bc = youtube.liveBroadcasts().list(part="snippet", broadcastStatus=status, maxResults=5).execute()
            print(f"🔍 [BOT] لقيت {len(bc['items'])} بث")
            for item in bc['items']:
                print(f"🔍 [BOT] بث: {item['snippet']['title']}")
                if 'liveChatId' in item['snippet']:
                    live_chat_id = item['snippet']['liveChatId']
                    print(f"✅ [BOT] لقيت الشات: {live_chat_id}")
                    break
            if live_chat_id: break
        
        if not live_chat_id:
            print("💀 [BOT] ما لقيتش شات. تأكد البث Public و شغال")
            return

        def send(text):
            try:
                youtube.liveChatMessages().insert(part="snippet", body={
                    "snippet": {"liveChatId": live_chat_id, "type": "textMessageEvent",
                    "textMessageDetails": {"messageText": text}}
                }).execute()
                print(f"📤 [BOT] بعثت: {text}")
            except Exception as e: print(f"💀 [SEND] {e}")

        send("🚫💸 البوت رجع! اكتب سلام 🚫💸")
        
        next_page_token = None
        while True:
            try:
                res = youtube.liveChatMessages().list(liveChatId=live_chat_id, part="snippet,authorDetails", pageToken=next_page_token).execute()
                print(f"📥 [BOT] جبت {len(res['items'])} رسائل")
                for item in res['items']:
                    msg = item['snippet']['displayMessage'].strip()
                    author = item['authorDetails']['displayName']
                    uid = item['authorDetails']['channelId']
                    if uid == bot_id: continue
                    print(f"📩 [{author}]: {msg}")
                    if msg == 'سلام': send(f"وعليكم السلام {author} 👋")
                    elif msg == 'بنق': send(f"Pong! ⚡🚫💸")
                next_page_token = res.get('nextPageToken')
                time.sleep(3)
            except Exception as e:
                print(f"💀 [LOOP] {e}")
                time.sleep(15)
                
    except Exception as e:
        print(f"💀 [BOT] كراش كبير: {e}")

if __name__ == "__main__":
    print("🚀 [MAIN] السيرفر يطلع...")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000))), daemon=True).start()
    threading.Thread(target=start_stream, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    print("🚀 [MAIN] كل الثريدات طلعت")
    while True: time.sleep(60)
