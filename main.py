import os, json, threading, time, subprocess
from flask import Flask
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# ========== الإعدادات ==========
TOKEN_JSON = os.getenv('TOKEN_JSON')
VIDEO_ID = os.getenv('VIDEO_ID')
STREAM_KEY = os.getenv('YT_STREAM_KEY') # المتغير تاعك
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2" # ثابت ديما
BOT_NAME = "🚫💸 INFINITY GEN"
PREFIX = "."
VIDEO_FILE = "video.mp4"

db = {'users': {}, 'games': {}, 'live_chat_id': None}

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
    'انتحاري': {'price': 1000, 'desc': 'تقتل 2 و تموت'},
    'حماية': {'price': 300, 'desc': 'تلغي تصويت ضدك مرة'}
}

def get_creds():
    creds_data = json.loads(TOKEN_JSON)
    creds = Credentials.from_authorized_user_info(creds_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        print("🔄 [BOT] جددت التوكن تلقائياً")
    return creds

def get_youtube():
    return build('youtube', 'v3', credentials=get_creds())

# ========== البث بـ YT_STREAM_KEY تاعك ==========
def start_ffmpeg_stream():
    if not STREAM_KEY:
        print("⚠️ [STREAM] YT_STREAM_KEY ناقص. ما نبثش")
        return

    full_rtmp = f"{RTMP_URL}/{STREAM_KEY}"
    print(f"📺 [STREAM] نبدا البث...")

    # 720p 24fps
    cmd = [
        'ffmpeg', '-re', '-stream_loop', '-1', '-i', VIDEO_FILE,
        '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '2000k',
        '-maxrate', '2000k', '-bufsize', '4000k', '-pix_fmt', 'yuv420p',
        '-r', '24', '-g', '48', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
        '-f', 'flv', full_rtmp
    ]

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ [FFMPEG] البث طلع بنجاح")
    except Exception as e:
        print(f"💀 [FFMPEG] كراش: {e}")

def send_msg(msg):
    try:
        if not db['live_chat_id']: return
        yt = get_youtube()
        yt.liveChatMessages().insert(
            part="snippet",
            body={"snippet": {
                "liveChatId": db['live_chat_id'],
                "type": "textMessageEvent",
                "textMessageDetails": {"messageText": msg[:200]}
            }}
        ).execute()
        print(f"📤 [BOT] {msg}")
    except Exception as e:
        print(f"💀 [SEND] {e}")

def add_points(user_id, user_name, pts):
    if user_id not in db['users']:
        db['users'][user_id] = {'points': 0, 'items': [], 'x2_until': None, 'name': user_name}
    user = db['users'][user_id]
    user['name'] = user_name
    if user['x2_until'] and datetime.now() < user['x2_until']:
        pts *= 2
    user['points'] += pts

def get_user(user_id):
    if user_id not in db['users']:
        db['users'][user_id] = {'points': 0, 'items': [], 'x2_until': None, 'name': 'مجهول'}
    return db['users'][user_id]

def anti_afk(game_id):
    time.sleep(80)
    game = db['games'].get(game_id)
    if game and len(game['players']) == 1:
        game['players']['bot_infinity'] = BOT_NAME
        send_msg(f"{BOT_NAME} دخلت باه نكسر الروتين 🚫💸")

def handle_cmd(author, msg):
    user_id = author['channelId']
    user_name = author['displayName']
    add_points(user_id, user_name, 1)

    if not msg.startswith(PREFIX): return
    parts = msg[1:].split()
    if not parts: return
    cmd = parts[0]
    args = parts[1:]

    if cmd == 'سلام': send_msg(f"وعليكم السلام {user_name} 🚫💸")
    elif cmd == 'بنق': send_msg("بونق 🚫💸 البوت حي 24/7")
    elif cmd == 'نقاطي': send_msg(f"💰 {user_name} رصيدك: {get_user(user_id)['points']} نقطة")
    elif cmd == 'توب':
        top = sorted(db['users'].items(), key=lambda x: x[1]['points'], reverse=True)[:10]
        txt = "👑 توب 10:\n" + "\n".join([f"{i}. {d['name']} - {d['points']}" for i, (_, d) in enumerate(top, 1)])
        send_msg(txt)
    elif cmd == 'متجر':
        txt = "🛒 المتجر النووي:\n" + "\n".join([f"{PREFIX}شراء {i} = {d['price']}" for i,d in SHOP.items()])
        send_msg(txt)
    elif cmd == 'شراء' and args:
        item = args[0]
        if item not in SHOP: return send_msg("❌ مكاش في المتجر")
        user = get_user(user_id)
        price = SHOP[item]['price']
        if user['points'] < price: return send_msg(f"❌ رصيدك ناقص. لازم {price}")
        user['points'] -= price
        if item == 'مضاعف':
            user['x2_until'] = datetime.now() + timedelta(seconds=SHOP[item]['duration'])
            send_msg(f"✅ {user_name} فعل المضاعف x2 لمدة 10د")
        else:
            user['items'].append(item)
            send_msg(f"✅ {user_name} شرا {item}")
    elif cmd == 'شنطة':
        items = get_user(user_id)['items']
        send_msg(f"🎒 شنطة {user_name}: {', '.join(items) if items else 'فارغة 🗿'}")
    elif cmd == 'xo' and 'start' in args:
        game_id = f"xo_{time.time()}"
        db['games'][game_id] = {'type': 'xo', 'players': {user_id: user_name}}
        send_msg(f"🎮 {user_name} فتح XO. اكتب {PREFIX}ادخل")
        threading.Thread(target=anti_afk, args=[game_id], daemon=True).start()

def get_live_chat_id(youtube):
    try:
        vid = VIDEO_ID
        if not vid:
            req = youtube.liveBroadcasts().list(part="id", broadcastStatus="active", broadcastType="all")
            res = req.execute()
            if not res['items']: return False
            vid = res['items'][0]['id']

        req = youtube.videos().list(part="liveStreamingDetails", id=vid)
        res = req.execute()
        db['live_chat_id'] = res['items'][0]['liveStreamingDetails']['activeLiveChatId']
        print(f"✅ [BOT] لقيت الشات: {db['live_chat_id']}")
        return True
    except Exception as e:
        print(f"🧟 [ZOMBIE] ما لقاش لايف: {e}")
        return False

def listen_chat():
    next_page_token = None
    while True:
        try:
            yt = get_youtube()
            if not db['live_chat_id']:
                if not get_live_chat_id(yt):
                    time.sleep(30)
                    continue
                send_msg(f"{BOT_NAME} طلع 24/7 🚫💸")

            req = yt.liveChatMessages().list(
                liveChatId=db['live_chat_id'],
                part="snippet,authorDetails",
                pageToken=next_page_token
            )
            res = req.execute()
            for item in res['items']:
                handle_cmd(item['authorDetails'], item['snippet']['displayMessage'])
            next_page_token = res.get('nextPageToken')
            time.sleep(res['pollingIntervalMillis'] / 1000)
        except Exception as e:
            print(f"💀 [LISTEN] {e}")
            db['live_chat_id'] = None
            next_page_token = None
            time.sleep(15)

def run_bot():
    print("🚀 [BOT] بدا الـ Thread تاع البوت")
    if not TOKEN_JSON: return print("💀 [BOT] TOKEN_JSON مكاش")

    # 1. شغل البث اذا YT_STREAM_KEY موجود
    start_ffmpeg_stream()

    # 2. شغل البوت تاع الشات
    print("🤖 [BOT] Credentials صحاح")
    print("🤖 [BOT] YouTube API جاهز")
    listen_chat()

@app.route('/')
def home(): return f"{BOT_NAME} حي 🚫💸"
@app.route('/ping')
def ping(): return "pong"

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
