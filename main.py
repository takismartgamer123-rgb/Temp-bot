from flask import Flask
import subprocess, threading, os, time, json, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return "INFINITY GEN Bot V2.1 Hunter 🚫💸"

DATA_FILE = 'data.json'
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"users": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid, name="مجهول"):
    data = load_data()
    if uid not in data["users"]:
        data["users"][uid] = {"points": 0, "name": name, "inventory": [], "multiplier_end": None, "wins": 0}
    data["users"][uid]["name"] = name
    return data["users"][uid]

def add_points(uid, name, amount):
    data = load_data()
    user = get_user(uid, name)
    if user["multiplier_end"] and datetime.now() < datetime.fromisoformat(user["multiplier_end"]):
        amount *= 2
    else:
        user["multiplier_end"] = None
    user["points"] += amount
    save_data(data)
    return user["points"]

SHOP = {"درع": {"price": 200, "desc": "درع 🛡️"}, "مضاعف": {"price": 500, "desc": "مضاعف x2 لمدة 10د ⏳"}}

def start_stream():
    stream_key = os.environ.get('YT_STREAM_KEY')
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '300k',
           '-s', '854x480', '-c:a', 'aac', '-b:a', '32k', '-f', 'flv', rtmp_url]
    print("📺 البث شغال")
    while True: subprocess.run(cmd); time.sleep(5)

active_games = {}
BOT_CHANNEL_ID = None

def start_bot():
    global BOT_CHANNEL_ID
    print("🤖 البوت الصياد يطلع...")
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get('TOKEN_JSON')))
    youtube = build('youtube', 'v3', credentials=creds)
    
    try:
        ch = youtube.channels().list(part="id", mine=True).execute()
        BOT_CHANNEL_ID = ch['items'][0]['id']
        print(f"✅ ID البوت: {BOT_CHANNEL_ID}")
    except Exception as e: 
        print(f"💀 خطأ ID: {e}")
        return

    live_chat_id = None
    while not live_chat_id:
        try:
            # نحوسو في كل الحالات: active + all + upcoming
            for status in ["active", "all", "upcoming"]:
                print(f"🔍 نحوس في {status}...")
                bc = youtube.liveBroadcasts().list(part="snippet", broadcastStatus=status, maxResults=10).execute()
                for item in bc['items']:
                    if 'liveChatId' in item['snippet']:
                        live_chat_id = item['snippet']['liveChatId']
                        title = item['snippet']['title']
                        print(f"✅ لقيت الشات في بث: {title}")
                        break
                if live_chat_id: break
            
            if not live_chat_id:
                print("⏳ ما لقيتش شات. نعاود بعد 10ث...")
                time.sleep(10)
        except Exception as e:
            print(f"💀 خطأ البحث: {e}")
            time.sleep(15)

    def send(text):
        try:
            youtube.liveChatMessages().insert(part="snippet", body={
                "snippet": {"liveChatId": live_chat_id, "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text}}
            }).execute()
            print(f"📤 {text}")
        except Exception as e: print(f"💀 Send: {e}")

    send("🚫💸 البوت الصياد طلع! | سلام | نقاطي | بنق | تخمين start")

    next_page_token = None
    while True:
        try:
            res = youtube.liveChatMessages().list(liveChatId=live_chat_id, part="snippet,authorDetails", pageToken=next_page_token).execute()
            for item in res['items']:
                msg = item['snippet']['displayMessage'].strip()
                author = item['authorDetails']['displayName']
                uid = item['authorDetails']['channelId']
                if uid == BOT_CHANNEL_ID: continue
                print(f"📩 {author}: {msg}")
                user = get_user(uid, author)
                add_points(uid, author, 1)

                if msg == 'سلام': send(f"وعليكم السلام {author} 👋")
                elif msg == 'نقاطي': send(f"{author} رصيدك: {user['points']} 💰")
                elif msg == 'بنق': send(f"Pong! ⚡🚫💸")
                elif msg == 'تخمين start' and live_chat_id not in active_games:
                    num = random.randint(1, 100)
                    active_games[live_chat_id] = {"type": "takhmin", "num": num}
                    send("🎲 تخمين بدا! رقم من 1 لـ 100 🚫💸")
                elif live_chat_id in active_games and msg.isdigit():
                    game = active_games[live_chat_id]
                    guess = int(msg)
                    if guess == game["num"]:
                        add_points(uid, author, 50)
                        send(f"🎉 {author} صحيح! +50 نقطة! 🚫💸")
                        del active_games[live_chat_id]
                    elif guess < game["num"]: send(f"📈 أكبر من {guess}")
                    else: send(f"📉 أصغر من {guess}")

            next_page_token = res.get('nextPageToken')
            time.sleep(3)
        except Exception as e:
            print(f"💀 Error: {e}")
            time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000))), daemon=True).start()
    threading.Thread(target=start_stream, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    while True: time.sleep(60)
