from flask import Flask
import subprocess, threading, os, time, json, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return "INFINITY GEN 24/7 Bot 🚫💸 | صنع في قالمة"

# ========= نظام البيانات =========
DATA_FILE = 'data.json'
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"users": {}, "games": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid):
    data = load_data()
    if uid not in data["users"]:
        data["users"][uid] = {"points": 0, "name": "مجهول", "inventory": [], "multiplier_end": None}
    return data["users"][uid]

def add_points(uid, name, amount):
    data = load_data()
    user = get_user(uid)
    user["name"] = name
    # تشيك المضاعف
    if user["multiplier_end"] and datetime.now() < datetime.fromisoformat(user["multiplier_end"]):
        amount *= 2
    else:
        user["multiplier_end"] = None
    user["points"] += amount
    save_data(data)
    return user["points"]

# ========= المتجر =========
SHOP = {
    "درع": {"price": 200, "desc": "درع 🛡️"},
    "مضاعف": {"price": 500, "desc": "مضاعف نقاط x2 لمدة 10د ⏳"},
    "كشف": {"price": 150, "desc": "كشف 🔍"},
    "قنبلة": {"price": 400, "desc": "قنبلة 💣"},
    "إنعاش": {"price": 700, "desc": "إنعاش ❤️‍🩹"}
}

# ========= البث =========
def start_stream():
    stream_key = os.environ.get('YT_STREAM_KEY')
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '300k',
           '-s', '854x480', '-c:a', 'aac', '-b:a', '32k', '-f', 'flv', rtmp_url]
    print("📺 [STREAM] بدا البث 🚫💸")
    while True: subprocess.run(cmd); time.sleep(5)

# ========= البوت =========
active_games = {}

def start_bot():
    print("🤖 [BOT] نعس على البث...")
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get('TOKEN_JSON')))
    youtube = build('youtube', 'v3', credentials=creds)
    live_chat_id = None

    while not live_chat_id:
        try:
            bc = youtube.liveBroadcasts().list(part="snippet", broadcastStatus="active").execute()
            if bc['items']:
                live_chat_id = bc['items'][0]['snippet']['liveChatId']
                print(f"✅ [BOT] لقيت البث!")
            else: time.sleep(3)
        except: time.sleep(10)

    def send(text):
        try:
            youtube.liveChatMessages().insert(part="snippet", body={
                "snippet": {"liveChatId": live_chat_id, "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text}}
            }).execute()
        except Exception as e: print(f"💀 {e}")

    def game_takhmin():
        num = random.randint(1, 100)
        active_games[live_chat_id] = {"type": "takhmin", "num": num, "tries": 0}
        send("🎲 بدات لعبة التخمين! خمن رقم من 1 لـ 100 🚫💸")

    def game_rps():
        active_games[live_chat_id] = {"type": "rps", "players": {}}
        send("✂️ حجر ورقة مقص! اكتبو: حجر او ورقة او مقص. النتيجة بعد 10 ثواني 🚫💸")
        threading.Timer(10, end_rps).start()

    def end_rps():
        if live_chat_id not in active_games: return
        game = active_games[live_chat_id]
        if len(game["players"]) < 2:
            send("😭 ما كفاوش اللاعبين. انتهت اللعبة")
        else:
            # منطق بسيط: عشوائي يربح
            winner_id = random.choice(list(game["players"].keys()))
            winner_name = game["players"][winner_id]["name"]
            add_points(winner_id, winner_name, 30)
            send(f"🎉 الفائز في حجر ورقة مقص هو @{winner_name}! +30 نقطة 🚫💸")
        del active_games[live_chat_id]

    next_page_token = None
    bot_start_time = time.time()
    game_started = False

    while True:
        try:
            res = youtube.liveChatMessages().list(liveChatId=live_chat_id, part="snippet,authorDetails", pageToken=next_page_token).execute()
            
            # يدخل الألعاب بعد 80 ثانية
            if not game_started and time.time() - bot_start_time > 80:
                game_started = True
                send("🎮 الألعاب تفعلت! اكتب: تخمين start او rps start 🚫💸")

            for item in res['items']:
                msg = item['snippet']['displayMessage'].strip()
                author = item['authorDetails']['displayName']
                uid = item['authorDetails']['channelId']
                points = add_points(uid, author, 1)
                user = get_user(uid)

                # === أوامر أساسية ===
                if msg == 'سلام': send(f"وعليكم السلام @{author} 👋")
                elif msg == 'نقاطي': send(f"@{author} رصيدك: {points} نقطة 💰")
                elif msg == 'بنق': send(f"Pong! ⚡🚫💸")
                elif msg == 'متجر':
                    shop_text = "🛒 المتجر النووي:\n" + "\n".join([f"شراء {k} = {v['price']} نقطة" for k, v in SHOP.items()])
                    send(shop_text)
                elif msg == 'شنطة':
                    inv = ", ".join(user["inventory"]) if user["inventory"] else "فارغة"
                    send(f"🎒 شنطة @{author}: {inv}")
                elif msg == 'مضاعف':
                    if "مضاعف" in user["inventory"]:
                        user["inventory"].remove("مضاعف")
                        user["multiplier_end"] = (datetime.now() + timedelta(minutes=10)).isoformat()
                        save_data(load_data())
                        send(f"⚡ @{author} فعلت المضاعف x2 لمدة 10د!")
                    else: send(f"@{author} ما عندكش مضاعف. اشريه بـ 500 نقطة")
                elif msg == 'توب':
                    data = load_data()
                    top = sorted(data["users"].items(), key=lambda x: x[1]["points"], reverse=True)[:10]
                    top_text = "👑 توب 10 جلادين:\n" + "\n".join([f"{i+1}. {u[1]['name']} - {u[1]['points']}" for i, u in enumerate(top)])
                    send(top_text)
                
                # === الشراء ===
                elif msg.startswith('شراء '):
                    item = msg.split('شراء ')[1]
                    if item in SHOP:
                        if user["points"] >= SHOP[item]["price"]:
                            user["points"] -= SHOP[item]["price"]
                            user["inventory"].append(item)
                            save_data(load_data())
                            send(f"✅ @{author} شريت {SHOP[item]['desc']} بـ {SHOP[item]['price']} نقطة 🚫💸")
                        else: send(f"❌ @{author} ما عندكش نقاط كافية")
                    else: send(f"❌ @{author} العنصر غير موجود")

                # === الألعاب ===
                elif msg == 'تخمين start' and game_started:
                    if live_chat_id not in active_games: game_takhmin()
                    else: send("⚠️ كاين لعبة جارية")
                elif msg == 'rps start' and game_started:
                    if live_chat_id not in active_games: game_rps()
                    else: send("⚠️ كاين لعبة جارية")
                
                # === منطق الألعاب ===
                elif live_chat_id in active_games:
                    game = active_games[live_chat_id]
                    if game["type"] == "takhmin" and msg.isdigit():
                        guess = int(msg)
                        game["tries"] += 1
                        if guess == game["num"]:
                            won = max(10, 50 - game["tries"] * 2)
                            add_points(uid, author, won)
                            send(f"🎉 @{author} صحيح! الرقم {game['num']}. ربحت {won} نقطة! 🚫💸")
                            del active_games[live_chat_id]
                        elif guess < game["num"]: send(f"📈 @{author} أكبر من {guess}")
                        else: send(f"📉 @{author} أصغر من {guess}")
                    
                    elif game["type"] == "rps" and msg in ['حجر', 'ورقة', 'مقص']:
                        game["players"][uid] = {"name": author, "choice": msg}
                        send(f"✅ @{author} اختار {msg}")

            next_page_token = res.get('nextPageToken')
            time.sleep(5)
        except Exception as e:
            print(f"💀 Error: {e}")
            time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000))), daemon=True).start()
    threading.Thread(target=start_stream, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    while True: time.sleep(60)
