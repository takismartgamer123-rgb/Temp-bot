import os, json, threading, time, random, requests
from flask import Flask
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# ========== الإعدادات ==========
TOKEN_JSON = os.getenv('TOKEN_JSON')
VIDEO_ID = os.getenv('VIDEO_ID') # اختياري
BOT_NAME = "🚫💸 INFINITY GEN"
PREFIX = "."

# ========== قاعدة البيانات ==========
db = {
    'users': {}, # {user_id: {'points': 0, 'items': [], 'x2_until': None}}
    'games': {}, # الألعاب الشغالة
    'live_chat_id': None
}

# ========== المتجر النووي ==========
SHOP = {
    'درع': {'price': 200, 'desc': 'يحميك من القتل مرة'},
    'مضاعف': {'price': 500, 'desc': 'x2 نقاط لمدة 10د', 'duration': 600},
    'كشف': {'price': 150, 'desc': 'يكشف دور لاعب في المافيا'},
    'قنبلة': {'price': 400, 'desc': 'تنقص 50 نقطة من الكل'},
    'كاتم': {'price': 600, 'desc': 'تمنع لاعب من الكلام جولة'},
    'درع_شرطي': {'price': 500, 'desc': 'حماية + كشف قاتل'},
    'إنعاش': {'price': 700, 'desc': 'ترجع لاعب ميت'},
    'تصويت_ذهبي': {'price': 350, 'desc': 'صوتك = 3 أصوات'},
    'جاسوس': {'price': 800, 'desc': 'تشوف شات المافيا'},
    'انتحاري': {'price': 1000, 'desc': 'تقتل 2 و تموت'}
}

# ========== دوال مساعدة ==========
def get_creds():
    creds_data = json.loads(TOKEN_JSON)
    creds = Credentials.from_authorized_user_info(creds_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_youtube():
    return build('youtube', 'v3', credentials=get_creds())

def send_msg(msg):
    try:
        yt = get_youtube()
        yt.liveChatMessages().insert(
            part="snippet",
            body={"snippet": {
                "liveChatId": db['live_chat_id'],
                "type": "textMessageEvent",
                "textMessageDetails": {"messageText": msg}
            }}
        ).execute()
        print(f"📤 [BOT] بعثت: {msg}")
    except Exception as e:
        print(f"💀 [BOT] خطأ في الإرسال: {e}")

def add_points(user_id, user_name, pts):
    if user_id not in db['users']:
        db['users'][user_id] = {'points': 0, 'items': [], 'x2_until': None, 'name': user_name}

    user = db['users'][user_id]
    # تشيك المضاعف
    if user['x2_until'] and datetime.now() < user['x2_until']:
        pts *= 2
    user['points'] += pts

def get_user(user_id):
    if user_id not in db['users']:
        db['users'][user_id] = {'points': 0, 'items': [], 'x2_until': None, 'name': 'مجهول'}
    return db['users'][user_id]

# ========== Anti-AFK 80 ثانية ==========
def anti_afk(game_id):
    time.sleep(80)
    game = db['games'].get(game_id)
    if game and len(game['players']) == 1:
        bot_id = 'bot_infinity'
        game['players'][bot_id] = BOT_NAME
        send_msg(f"{BOT_NAME} دخلت باه نكسر الروتين 🚫💸")
        start_game(game_id)

# ========== معالجة الأوامر ==========
def handle_cmd(author, msg):
    user_id = author['channelId']
    user_name = author['displayName']
    add_points(user_id, user_name, 1) # كل رسالة +1 نقطة

    if not msg.startswith(PREFIX):
        return

    cmd = msg[1:].split()[0]
    args = msg[1:].split()[1:]

    # أوامر أساسية
    if cmd == 'سلام':
        send_msg(f"وعليكم السلام {user_name} 🚫💸")

    elif cmd == 'نقاطي':
        pts = get_user(user_id)['points']
        send_msg(f"{user_name} رصيدك: {pts} نقطة 💰")

    elif cmd == 'توب':
        top = sorted(db['users'].items(), key=lambda x: x[1]['points'], reverse=True)[:10]
        txt = "👑 توب 10 جلادين:\n"
        for i, (uid, data) in enumerate(top, 1):
            txt += f"{i}. {data['name']} - {data['points']} نقطة\n"
        send_msg(txt)

    elif cmd == 'بنق':
        send_msg("بونق 🚫💸 البوت حي")

    elif cmd == 'متجر':
        txt = "🛒 المتجر النووي:\n"
        for item, data in SHOP.items():
            txt += f"{PREFIX}شراء {item} = {data['price']} نقطة - {data['desc']}\n"
        send_msg(txt)

    elif cmd == 'شراء' and args:
        item = args[0]
        if item not in SHOP:
            send_msg("هذا العنصر مكاش في المتجر 🚫💸")
            return
        user = get_user(user_id)
        price = SHOP[item]['price']
        if user['points'] < price:
            send_msg(f"رصيدك ناقص يا {user_name}. لازم {price} نقطة")
            return
        user['points'] -= price
        if item == 'مضاعف':
            user['x2_until'] = datetime.now() + timedelta(seconds=SHOP[item]['duration'])
        else:
            user['items'].append(item)
        send_msg(f"✅ {user_name} شرا {item} بـ {price} نقطة")

    elif cmd == 'شنطة':
        items = get_user(user_id)['items']
        if not items:
            send_msg(f"{user_name} شنطتك فارغة 🗿")
        else:
            send_msg(f"🎒 شنطة {user_name}: {', '.join(items)}")

    # لعبة XO كمثال
    elif cmd == 'xo':
        if 'start' in args:
            game_id = f"xo_{time.time()}"
            db['games'][game_id] = {'type': 'xo', 'players': {user_id: user_name}, 'board': ['1','2','3','4','5','6','7','8','9']}
            send_msg(f"🎮 {user_name} فتح طاولة XO. اكتب {PREFIX}ادخل للدخول")
            threading.Thread(target=anti_afk, args=[game_id]).start()

    elif cmd == 'ادخل':
        for gid, game in db['games'].items():
            if user_id not in game['players']:
                game['players'][user_id] = user_name
                send_msg(f"{user_name} دخل للعبة ✅")
                if len(game['players']) == 2:
                    start_game(gid)
                return
        send_msg("مكاش لعبة مفتوحة ضرك")

def start_game(game_id):
    game = db['games'][game_id]
    if game['type'] == 'xo':
        board = game['board']
        send_msg(f"🎮 XO بدات:\n{board[0]}|{board[1]}|{board[2]}\n{board[3]}|{board[4]}|{board[5]}\n{board[6]}|{board[7]}|{board[8]}")

# ========== الحماية ضد الزومبي الأطرش ==========
def get_live_chat_id(youtube):
    global db
    try:
        if VIDEO_ID:
            vid = VIDEO_ID
        else:
            # جيب اللايف تاع قناتك تلقائي
            req = youtube.liveBroadcasts().list(part="snippet", broadcastStatus="active", broadcastType="all")
            res = req.execute()
            if not res['items']:
                return None
            vid = res['items'][0]['id']

        req = youtube.videos().list(part="liveStreamingDetails", id=vid)
        res = req.execute()
        db['live_chat_id'] = res['items'][0]['liveStreamingDetails']['activeLiveChatId']
        return True
    except:
        return False

def listen_chat():
    fail_count = 0
    while True:
        try:
            yt = get_youtube()

            # حماية الزومبي: اذا 3 دقايق ما لقاش الشات يعاود
            if not db['live_chat_id']:
                if not get_live_chat_id(yt):
                    fail_count += 1
                    if fail_count >= 3:
                        print("🧟 [BOT] الزومبي الأطرش! نعاود بعد 60ث")
                        time.sleep(60)
                        fail_count = 0
                    time.sleep(20)
                    continue

            fail_count = 0
            req = yt.liveChatMessages().list(liveChatId=db['live_chat_id'], part="snippet,authorDetails")
            res = req.execute()

            for item in res['items']:
                msg = item['snippet']['displayMessage']
                author = item['authorDetails']
                handle_cmd(author, msg)

            time.sleep(5)

        except Exception as e:
            print(f"💀 [BOT] خطأ: {e}")
            db['live_chat_id'] = None # حماية الزومبي
            time.sleep(15)

# ========== تشغيل البوت ==========
def run_bot():
    print("🚀 [BOT] بدا الـ Thread تاع البوت")
    if not TOKEN_JSON:
        print("💀 [BOT] TOKEN_JSON مكاش")
        return
    print("✅ [BOT] لقيت TOKEN_JSON")
    print("🤖 [BOT] Credentials صحاح")
    print("🤖 [BOT] YouTube API جاهز")
    listen_chat()

@app.route('/')
def home():
    return f"{BOT_NAME} حي 24/7 🚫💸"

@app.route('/ping')
def ping():
    return "pong" # لـ UptimeRobot

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
