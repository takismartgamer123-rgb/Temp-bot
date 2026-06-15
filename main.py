from flask import Flask
import subprocess, threading, os, time, json, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return "INFINITY GEN 24/7 Bot V3 FURY 🚫💸"

# ========= البيانات data.json =========
DATA_FILE = 'data.json'
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"users": {}, "games": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid, name="مجهول"):
    data = load_data()
    if uid not in data["users"]:
        data["users"][uid] = {"points": 0, "name": name, "inventory": [], "multiplier_end": None, "wins": 0, "alive": True}
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

# ========= المتجر النووي الكامل =========
SHOP = {
    "درع": {"price": 200, "desc": "درع 🛡️"},
    "مضاعف": {"price": 500, "desc": "مضاعف x2 لمدة 10د ⏳"},
    "كشف": {"price": 150, "desc": "كشف 🔍"},
    "قنبلة": {"price": 400, "desc": "قنبلة 💣"},
    "كاتم": {"price": 600, "desc": "كاتم للمافيا 🤫"},
    "درع_شرطي": {"price": 500, "desc": "درع شرطي 👮"},
    "إنعاش": {"price": 700, "desc": "إنعاش ❤️‍🩹"},
    "تصويت_ذهبي": {"price": 350, "desc": "تصويت ذهبي 🗳️"},
    "جاسوس": {"price": 800, "desc": "جاسوس 🕵️"},
    "انتحاري": {"price": 1000, "desc": "انتحاري 💀"}
}

WORDS = ["قالمة", "نووي", "جلاد", "بوت", "يوتيوب", "نقاط", "متجر", "انفينيتي", "اسطورة", "جزائر", "مملكة", "قنبلة", "مافيا", "كنز"]
QUESTIONS = [
    {"q": "عاصمة الجزائر؟", "a": "الجزائر"},
    {"q": "كم ولاية في الجزائر؟", "a": "58"},
    {"q": "اسم بوتنا؟", "a": "انفينيتي"},
    {"q": "ولاية 24؟", "a": "قالمة"}
]

# ========= البث =========
def start_stream():
    stream_key = os.environ.get('YT_STREAM_KEY')
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '300k',
           '-s', '854x480', '-c:a', 'aac', '-b:a', '32k', '-f', 'flv', rtmp_url]
    while True: subprocess.run(cmd); time.sleep(5)

# ========= البوت =========
active_games = {}

def start_bot():
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
        except: pass

    # ===== دوال الألعاب 1-16 =====
    def game_xo(): 
        b = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣"]
        active_games[live_chat_id] = {"type": "xo", "board": b, "turn": "X"}
        send(f"🎮 XO بدات!\n{b[0]}{b[1]}{b[2]}\n{b[3]}{b[4]}{b[5]}\n{b[6]}{b[7]}{b[8]}\nاكتب xo 1-9")

    def game_mafia():
        active_games[live_chat_id] = {"type": "mafia", "players": {}, "started": False, "phase": "lobby"}
        send("🎭 لوبي مافيا انطلق! اكتب 'ادخل' للدخول. 4 لاعبين على الأقل. تبدا بعد 30ث 🚫💸")
        threading.Timer(30, start_mafia).start()

    def start_mafia():
        if live_chat_id not in active_games or active_games[live_chat_id]["type"]!= "mafia": return
        game = active_games[live_chat_id]
        if len(game["players"]) < 4: 
            send("😭 ما كفاوش اللاعبين للمافيا"); del active_games[live_chat_id]; return
        game["started"] = True
        players = list(game["players"].keys())
        random.shuffle(players)
        game["mafia"] = players[0]
        game["doctor"] = players[1] if len(players) > 1 else None
        game["phase"] = "night"
        send(f"🌙 ليل المافيا بدا! المافيا: سري | الطبيب: سري\nالمافيا اكتب 'قتل @اسم' | الطبيب 'انقذ @اسم'")

    def game_rps():
        active_games[live_chat_id] = {"type": "rps", "players": {}}
        send("✂️ حجر ورقة مقص! اكتبو: حجر او ورقة او مقص. النتيجة بعد 10 ثواني 🚫💸")
        threading.Timer(10, end_rps).start()

    def end_rps():
        if live_chat_id not in active_games: return
        game = active_games[live_chat_id]
        if len(game["players"]) < 2: send("😭 ما كفاوش اللاعبين")
        else:
            winner_id = random.choice(list(game["players"].keys()))
            winner_name = game["players"][winner_id]["name"]
            add_points(winner_id, winner_name, 30)
            get_user(winner_id)["wins"] += 1; save_data(load_data())
            send(f"🎉 الفائز في حجر ورقة مقص هو {winner_name}! +30 نقطة 🚫💸")
        del active_games[live_chat_id]

    def game_takhmin():
        num = random.randint(1, 100)
        active_games[live_chat_id] = {"type": "takhmin", "num": num, "tries": 0}
        send("🎲 بدات لعبة التخمين! خمن رقم من 1 لـ 100 🚫💸")

    def game_kalima():
        word = random.choice(WORDS)
        active_games[live_chat_id] = {"type": "kalima", "word": word}
        hidden = word[0] + "ـ" * (len(word)-2) + word[-1] if len(word) > 2 else word
        send(f"📖 كلمة السر بدات! الكلمة: {hidden} | {len(word)} حروف 🚫💸")

    def game_3ajala():
        active_games[live_chat_id] = {"type": "3ajala", "spins": {}}
        send("🎡 عجلة الحظ! اكتب 'دور' باه تدور. مرة وحدة لكل لاعب 🚫💸")

    def game_soual():
        q = random.choice(QUESTIONS)
        active_games[live_chat_id] = {"type": "soual", "q": q}
        send(f"🎤 سؤال وجواب: {q['q']} 🚫💸")

    def game_kataba():
        text = random.choice(["بوت انفينيتي اسطوري", "قالمة ولاية النووي", "جلادين اليوتيوب هنا"])
        active_games[live_chat_id] = {"type": "kataba", "text": text, "start": time.time()}
        send(f"⌨️ سباق كتابة! اكتب:\n{text} 🚫💸")

    def game_kalimat():
        active_games[live_chat_id] = {"type": "kalimat", "words": {}, "start": time.time()}
        send("⚡ حرب كلمات 60ث! اكتب اكبر عدد كلمات مختلفة. ابدا ضرك! 🚫💸")
        threading.Timer(60, end_kalimat).start()

    def end_kalimat():
        if live_chat_id not in active_games: return
        game = active_games[live_chat_id]
        if not game["words"]: send("😭 حتى واحد ما كتب")
        else:
            winner = max(game["words"], key=game["words"].get)
            winner_data = get_user(winner)
            won = game["words"][winner] * 5
            add_points(winner, winner_data["name"], won)
            send(f"🏆 {winner_data['name']} فاز في حرب الكلمات! {game['words'][winner]} كلمة | +{won} نقطة 🚫💸")
        del active_games[live_chat_id]

    def game_million():
        active_games[live_chat_id] = {"type": "million", "step": 0}
        send("💰 من سيربح النقاط! اول سؤال: عاصمة الجزائر؟ أ: وهران ب: الجزائر ج: قسنطينة 🚫💸")

    def game_kanz():
        active_games[live_chat_id] = {"type": "kanz", "pos": random.randint(1, 9)}
        send("🗺️ كنز قالمة! الكنز مخبي في رقم من 1-9. اكتب 'كنز 5' مثلا 🚫💸")

    def game_sijn():
        active_games[live_chat_id] = {"type": "sijn", "players": []}
        send("⛓️ سجن و جلاد! اكتب 'ادخل' للدخول. نختار جلاد عشوائي بعد 15ث 🚫💸")
        threading.Timer(15, start_sijn).start()

    def start_sijn():
        if live_chat_id not in active_games: return
        game = active_games[live_chat_id]
        if len(game["players"]) < 2: send("😭 ما كفاوش للسجن")
        else:
            jalad = random.choice(game["players"])
            game["jalad"] = jalad["uid"]
            send(f"👨‍⚖️ الجلاد هو {jalad['name']}! اكتب 'اسجن @اسم' باه تسجن واحد 🚫💸")
        del active_games[live_chat_id]

    def game_sor3a():
        num1, num2 = random.randint(10, 50), random.randint(10, 50)
        active_games[live_chat_id] = {"type": "sor3a", "ans": num1 + num2}
        send(f"⚡ تحدي سرعة! حل: {num1} + {num2} = ؟ 🚫💸")

    def game_qatil():
        active_games[live_chat_id] = {"type": "qatil", "killer": None}
        send("🔪 من القاتل! واحد منكم هو القاتل. اكتب 'اتهم @اسم' 🚫💸")

    def game_borsa():
        price = random.randint(50, 200)
        active_games[live_chat_id] = {"type": "borsa", "price": price, "holders": {}}
        send(f"📈 بورصة النقاط! سعر السهم ضرك: {price}. اكتب 'بيع' او 'شراء' 🚫💸")

    def game_mamlaka():
        active_games[live_chat_id] = {"type": "mamlaka", "king": None}
        send("🏰 مملكة الجلادين! اول واحد يكتب 'انا الملك' يولي ملك ويجمع الضرائب 🚫💸")

    next_page_token = None

    while True:
        try:
            res = youtube.liveChatMessages().list(liveChatId=live_chat_id, part="snippet,authorDetails", pageToken=next_page_token).execute()
            
            for item in res['items']:
                msg = item['snippet']['displayMessage'].strip()
                author = item['authorDetails']['displayName']
                uid = item['authorDetails']['channelId']
                user = get_user(uid, author)
                points = add_points(uid, author, 1)

                # === أساسية ===
                if msg == 'سلام': send(f"وعليكم السلام {author} 👋")
                elif msg == 'نقاطي': send(f"{author} رصيدك: {user['points']} 💰 | فوز: {user['wins']}")
                elif msg == 'بنق': send(f"Pong! ⚡🚫💸")
                elif msg == 'متجر': send("🛒 المتجر:\n" + "\n".join([f"شراء {k} = {v['price']}" for k, v in SHOP.items()]))
                elif msg == 'شنطة': send(f"🎒 شنطة {author}: {', '.join(user['inventory']) or 'فارغة'}")
                elif msg == 'مضاعف':
                    if "مضاعف" in user["inventory"]:
                        user["inventory"].remove("مضاعف")
                        user["multiplier_end"] = (datetime.now() + timedelta(minutes=10)).isoformat()
                        save_data(load_data())
                        send(f"⚡ {author} فعلت المضاعف x2!")
                    else: send(f"{author} ما عندكش مضاعف")
                elif msg == 'توب':
                    data = load_data()
                    top = sorted(data["users"].items(), key=lambda x: x[1]["points"], reverse=True)[:10]
                    top_text = "👑 توب 10:\n" + "\n".join([f"{i+1}. {u[1]['name']} - {u[1]['points']}" for i, u in enumerate(top)])
                    send(top_text)
                
                # === شراء ===
                elif msg.startswith('شراء '):
                    item = msg.split('شراء ')[1]
                    if item in SHOP and user["points"] >= SHOP[item]["price"]:
                        user["points"] -= SHOP[item]["price"]
                        user["inventory"].append(item)
                        save_data(load_data())
                        send(f"✅ {author} شريت {SHOP[item]['desc']} 🚫💸")
                    else: send(f"❌ {author} ما تقدرش تشري")

                # === بدء الألعاب 1-16 فوري ===
                elif live_chat_id not in active_games:
                    if msg == 'xo start': game_xo()
                    elif msg == 'مافيا start': game_mafia()
                    elif msg == 'rps start': game_rps()
                    elif msg == 'تخمين start': game_takhmin()
                    elif msg == 'كلمة start': game_kalima()
                    elif msg == 'عجلة start': game_3ajala()
                    elif msg == 'سؤال start': game_soual()
                    elif msg == 'كتابة start': game_kataba()
                    elif msg == 'كلمات start': game_kalimat()
                    elif msg == 'مليون start': game_million()
                    elif msg == 'كنز start': game_kanz()
                    elif msg == 'سجن start': game_sijn()
                    elif msg == 'سرعة start': game_sor3a()
                    elif msg == 'قاتل start': game_qatil()
                    elif msg == 'بورصة start': game_borsa()
                    elif msg == 'مملكة start': game_mamlaka()
                
                # === ادخل ===
                elif msg == 'ادخل' and live_chat_id in active_games:
                    game = active_games[live_chat_id]
                    if game["type"] == "mafia" and not game["started"]:
                        game["players"][uid] = {"name": author}
                        send(f"✅ {author} دخل للمافيا")
                    elif game["type"] == "sijn":
                        game["players"].append({"uid": uid, "name": author})
                        send(f"✅ {author} دخل للسجن")

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
                    
                    elif t == "kalima" and msg == game["word"]:
                        add_points(uid, author, 40); user["wins"] += 1; save_data(load_data())
                        send(f"🎉 {author} جاب كلمة السر! +40 نقطة 🚫💸")
                        del active_games[live_chat_id]
                    
                    elif t == "3ajala" and msg == "دور":
                        if uid not in game["spins"]:
                            prize = random.choice([10, 20, 50, 100, 0, 200, 5, 0])
                            game["spins"][uid] = True
                            if prize > 0:
                                add_points(uid, author, prize)
                                send(f"🎡 {author} ربحت {prize} نقطة! 🚫💸")
                            else: send(f"🎡 {author} خسرت 😭")
                    
                    elif t == "soual" and msg == game["q"]["a"]:
                        add_points(uid, author, 25); user["wins"] += 1; save_data(load_data())
                        send(f"✅ {author} جاوب صح! +25 نقطة 🚫💸")
                        del active_games[live_chat_id]
                    
                    elif t == "kataba" and msg == game["text"]:
                        elapsed = time.time() - game["start"]
                        won = max(10, int(60 - elapsed))
                        add_points(uid, author, won); user["wins"] += 1; save_data(load_data())
                        send(f"⌨️ {author} فاز! {elapsed:.1f}ث | +{won} نقطة 🚫💸")
                        del active_games[live_chat_id]
                    
                    elif t == "kalimat":
                        game["words"][uid] = game["words"].get(uid, 0) + 1
                    
                    elif t == "kanz" and msg.startswith('كنز '):
                        try:
                            pos = int(msg.split('كنز ')[1])
                            if pos == game["pos"]:
                                add_points(uid, author, 100); user["wins"] += 1; save_data(load_data())
                                send(f"💎 {author} لقى كنز قالمة! +100 نقطة 🚫💸")
                                del active_games[live_chat_id]
                            else: send(f"❌ {author} ماكانش هنا")
                        except: pass
                    
                    elif t == "sor3a" and msg.isdigit() and int(msg) == game["ans"]:
                        add_points(uid, author, 30); user["wins"] += 1; save_data(load_data())
                        send(f"⚡ {author} الأسرع! +30 نقطة 🚫💸")
                        del active_games[live_chat_id]
                    
                    elif t == "mamlaka" and msg == "انا الملك" and not game["king"]:
                        game["king"] = uid
                        send(f"👑 {author} هو ملك المملكة ضرك! اكتب 'ضريبة' لجمع 10 نقاط من كل واحد 🚫💸")
                    
                    elif t == "mamlaka" and msg == "ضريبة" and game["king"] == uid:
                        data = load_data()
                        tax = 0
                        for u in data["users"].values():
                            if u["points"] >= 10: u["points"] -= 10; tax += 10
                        user["points"] += tax; save_data(data)
                        send(f"💰 الملك {author} جمع {tax} نقطة ضريبة! 🚫💸")

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
