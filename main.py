from flask import Flask
import subprocess, threading, os, time, json, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return "INFINITY GEN Bot V2 Stable 🚫💸"

# ========= البيانات =========
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

# ========= المتجر الخفيف =========
SHOP = {
    "درع": {"price": 200, "desc": "درع 🛡️"},
    "مضاعف": {"price": 500, "desc": "مضاعف x2 لمدة 10د ⏳"},
    "قنبلة": {"price": 400, "desc": "قنبلة 💣"}
}

# ========= البث =========
def start_stream():
    stream_key = os.environ.get('YT_STREAM_KEY')
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '300k',
           '-s', '854x480', '-c:a', 'aac', '-b:a', '32k', '-f', 'flv', rtmp_url]
    print("📺 البث شغال")
    while True: subprocess.run(cmd); time.sleep(5)

# ========= البوت =========
active_games = {}
BOT_CHANNEL_ID = None

def start_bot():
    global BOT_CHANNEL_ID
    print("🤖 البوت يطلع...")
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
            bc = youtube.liveBroadcasts().list(part="snippet", broadcastStatus="active").execute()
            if bc['items']:
                live_chat_id = bc['items'][0]['snippet']['liveChatId']
                print(f"✅ لقيت الشات")
            else: 
                print("⏳ نستنى في لايف...")
                time.sleep(5)
        except: time.sleep(10)

    def send(text):
        try:
            youtube.liveChatMessages().insert(part="snippet", body={
                "snippet": {"liveChatId": live_chat_id, "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text}}
            }).execute()
            print(f"📤 {text}")
        except Exception as e: print(f"💀 Send: {e}")

    send("🚫💸 البوت V2 طلع! الأوامر: سلام | نقاطي | بنق | توب | متجر | تخمين start | xo start | rps start")

    # ===== الألعاب الخفيفة لي كانت خدامة =====
    def game_takhmin():
        num = random.randint(1, 100)
        active_games[live_chat_id] = {"type": "takhmin", "num": num, "tries": 0}
        send("🎲 تخمين بدا! رقم من 1 لـ 100 🚫💸")

    def game_xo(): 
        b = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣"]
        active_games[live_chat_id] = {"type": "xo", "board": b, "turn": "X"}
        send(f"🎮 XO بدات!\n{b[0]}{b[1]}{b[2]}\n{b[3]}{b[4]}{b[5]}\n{b[6]}{b[7]}{b[8]}\nاكتب xo 1-9")

    def game_rps():
        active_games[live_chat_id] = {"type": "rps", "players": {}}
        send("✂️ حجر ورقة مقص! اكتبو: حجر او ورقة او مقص. النتيجة بعد 10ث 🚫💸")
        threading.Timer(10, end_rps).start()

    def end_rps():
        if live_chat_id not in active_games: return
        game = active_games[live_chat_id]
        if len(game["players"]) < 2: send("😭 ما كفاوش اللاعبين")
        else:
            winner_id = random.choice(list(game["players"].keys()))
            winner_name = game["players"][winner_id]["name"]
            add_points(winner_id, winner_name, 30)
            send(f"🎉 الفائز هو {winner_name}! +30 نقطة 🚫💸")
        del active_games[live_chat_id]

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
                points = add_points(uid, author, 1)

                # === أوامر أساسية خدامة 100% ===
                if msg == 'سلام': send(f"وعليكم السلام {author} 👋")
                elif msg == 'نقاطي': send(f"{author} رصيدك: {user['points']} 💰 | فوز: {user['wins']}")
                elif msg == 'بنق': send(f"Pong! ⚡🚫💸")
                elif msg == 'توب':
                    data = load_data()
                    top = sorted(data["users"].items(), key=lambda x: x[1]["points"], reverse=True)[:10]
                    top_text = "👑 توب 10:\n" + "\n".join([f"{i+1}. {u[1]['name']} - {u[1]['points']}" for i, u in enumerate(top)])
                    send(top_text)
                
                # === المتجر ===
                elif msg == 'متجر': send("🛒 المتجر:\n" + "\n".join([f"شراء {k} = {v['price']}" for k, v in SHOP.items()]))
                elif msg == 'شنطة': send(f"🎒 شنطة {author}: {', '.join(user['inventory']) or 'فارغة'}")
                elif msg == 'مضاعف':
                    if "مضاعف" in user["inventory"]:
                        user["inventory"].remove("مضاعف")
                        user["multiplier_end"] = (datetime.now() + timedelta(minutes=10)).isoformat()
                        save_data(load_data())
                        send(f"⚡ {author} فعلت المضاعف x2 لمدة 10د!")
                    else: send(f"{author} ما عندكش مضاعف. اشريه من المتجر")
                elif msg.startswith('شراء '):
                    item = msg.split('شراء ')[1]
                    if item in SHOP and user["points"] >= SHOP[item]["price"]:
                        user["points"] -= SHOP[item]["price"]
                        user["inventory"].append(item)
                        save_data(load_data())
                        send(f"✅ {author} شريت {SHOP[item]['desc']} 🚫💸")
                    else: send(f"❌ {author} نقاطك ما تكفيش")

                # === الألعاب الخفيفة ===
                elif live_chat_id not in active_games:
                    if msg == 'تخمين start': game_takhmin()
                    elif msg == 'xo start': game_xo()
                    elif msg == 'rps start': game_rps()
                
                # === منطق الألعاب ===
                elif live_chat_id in active_games:
                    game = active_games[live_chat_id]
                    t = game["type"]
                    
                    if t == "takhmin" and msg.isdigit():
                        guess = int(msg); game["tries"] += 1
                        if guess == game["num"]:
                            won = max(10, 50 - game["tries"] * 2)
                            add_points(uid, author, won); user["wins"] += 1; save_data(load_data())
                            send(f"🎉 {author} صحيح! الرقم {game['num']}. +{won} نقطة! 🚫💸")
                            del active_games[live_chat_id]
                        elif guess < game["num"]: send(f"📈 {author} أكبر من {guess}")
                        else: send(f"📉 {author} أصغر من {guess}")
                    
                    elif t == "rps" and msg in ['حجر', 'ورقة', 'مقص']:
                        game["players"][uid] = {"name": author, "choice": msg}
                        send(f"✅ {author} اختار {msg}")
                    
                    elif t == "xo" and msg.startswith('xo '):
                        try:
                            pos = int(msg.split('xo ')[1]) - 1
                            if 0 <= pos <= 8 and game["board"][pos] not in ["❌","⭕"]:
                                symbol = "❌" if game["turn"] == "X" else "⭕"
                                game["board"][pos] = symbol
                                game["turn"] = "O" if game["turn"] == "X" else "X"
                                b = game["board"]; wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
                                winner = None
                                for w in wins:
                                    if b[w[0]] == b[w[1]] == b[w[2]] and b[w[0]] in ["❌","⭕"]: winner = b[w[0]]
                                show = f"{b[0]}{b[1]}{b[2]}\n{b[3]}{b[4]}{b[5]}\n{b[6]}{b[7]}{b[8]}"
                                if winner:
                                    add_points(uid, author, 50); user["wins"] += 1; save_data(load_data())
                                    send(f"🎉 {author} ربح في XO! +50 نقطة\n{show}")
                                    del active_games[live_chat_id]
                                elif all(x in ["❌","⭕"] for x in b):
                                    send(f"🤝 تعادل!\n{show}"); del active_games[live_chat_id]
                                else: send(f"دور {game['turn']}\n{show}")
                        except: pass

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
