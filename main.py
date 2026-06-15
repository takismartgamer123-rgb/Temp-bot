import os, json, threading, time, random, subprocess
from flask import Flask
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)
TOKEN_JSON = os.getenv('TOKEN_JSON')
BOT_NAME = "🚫💸 INFINITY GEN"
PREFIX = "."

db = {'users': {}, 'games': {}, 'live_chat_id': None, 'video_id': None}

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

def get_creds():
    creds_data = json.loads(TOKEN_JSON)
    creds = Credentials.from_authorized_user_info(creds_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_youtube():
    return build('youtube', 'v3', credentials=get_creds())

def start_youtube_stream():
    yt = get_youtube()
    broadcast = yt.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {"title": f"{BOT_NAME} 24/7", "scheduledStartTime": datetime.utcnow().isoformat() + "Z"},
            "status": {"privacyStatus": "public"},
            "contentDetails": {"enableAutoStart": True, "enableDvr": True}
        }
    ).execute()

    stream = yt.liveStreams().insert(
        part="snippet,cdn",
        body={
            "snippet": {"title": "INFINITY Stream"},
            "cdn": {"ingestionType": "rtmp", "resolution": "720p", "frameRate": "30fps"}
        }
    ).execute()

    yt.liveBroadcasts().bind(part="id", id=broadcast["id"], streamId=stream["id"]).execute()
    rtmp_url = stream['cdn']['ingestionInfo']['ingestionAddress']
    stream_key = stream['cdn']['ingestionInfo']['streamName']
    full_rtmp = f"{rtmp_url}/{stream_key}"

    print(f"📺 [STREAM] لايف جديد: https://youtube.com/watch?v={broadcast['id']}")

    # بث video.mp4 720p 24fps لوب
    cmd = [
        'ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
        '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '2000k',
        '-maxrate', '2000k', '-bufsize', '4000k', '-pix_fmt', 'yuv420p',
        '-r', '24', '-g', '48', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
        '-f', 'flv', full_rtmp
    ]
    subprocess.Popen(cmd)
    db['video_id'] = broadcast["id"]
    return broadcast["id"]

def send_msg(msg):
    try:
        yt = get_youtube()
        yt.liveChatMessages().insert(
            part="snippet",
            body={"snippet": {"liveChatId": db['live_chat_id'], "type": "textMessageEvent", "textMessageDetails": {"messageText": msg}}}
        ).execute()
        print(f"📤 [BOT] بعثت: {msg}")
    except Exception as e:
        print(f"💀 [BOT] خطأ في الإرسال: {e}")

def add_points(user_id, user_name, pts):
    if user_id not in db['users']:
        db['users'][user_id] = {'points': 0, 'items': [], 'x2_until': None, 'name': user_name}
    user = db['users'][user_id]
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
    cmd = msg[1:].split()[0]
    args = msg[1:].split()[1:]

    if cmd == 'سلام': send_msg(f"وعليكم السلام {user_name} 🚫💸")
    elif cmd == 'نقاطي': send_msg(f"{user_name} رصيدك: {get_user(user_id)['points']} نقطة 💰")
    elif cmd == 'بنق': send_msg("بونق 🚫💸 البوت حي")
    elif cmd == 'توب':
        top = sorted(db['users'].items(), key=lambda x: x[1]['points'], reverse=True)[:5]
        txt = "👑 توب 5:\n" + "\n".join([f"{i}. {d['name']} - {d['points']}" for i, (_, d) in enumerate(top, 1)])
        send_msg(txt)
    elif cmd == 'متجر':
        txt = "🛒 المتجر:\n" + "\n".join([f"{PREFIX}شراء {i} = {d['price']}" for i,d in SHOP.items()])
        send_msg(txt)
    elif cmd == 'شراء' and args:
        item = args[0]
        if item not in SHOP: return send_msg("مكاش في المتجر 🚫💸")
        user = get_user(user_id)
        price = SHOP[item]['price']
        if user['points'] < price: return send_msg(f"رصيدك ناقص. لازم {price}")
        user['points'] -= price
        if item == 'مضاعف': user['x2_until'] = datetime.now() + timedelta(seconds=SHOP[item]['duration'])
        else: user['items'].append(item)
        send_msg(f"✅ {user_name} شرا {item}")
    elif cmd == 'شنطة':
        items = get_user(user_id)['items']
        send_msg(f"🎒 شنطة {user_name}: {', '.join(items) if items else 'فارغة'}")
    elif cmd == 'xo' and 'start' in args:
        game_id = f"xo_{time.time()}"
        db['games'][game_id] = {'type': 'xo', 'players': {user_id: user_name}}
        send_msg(f"🎮 {user_name} فتح XO. اكتب {PREFIX}ادخل")
        threading.Thread(target=anti_afk, args=[game_id]).start()

def get_live_chat_id(youtube):
    try:
        req = youtube.videos().list(part="liveStreamingDetails", id=db['video_id'])
        res = req.execute()
        db['live_chat_id'] = res['items'][0]['liveStreamingDetails']['activeLiveChatId']
        return True
    except: return False

def listen_chat():
    while True:
        try:
            yt = get_youtube()
            if not db['live_chat_id']:
                if not get_live_chat_id(yt):
                    time.sleep(20)
                    continue
            req = yt.liveChatMessages().list(liveChatId=db['live_chat_id'], part="snippet,authorDetails")
            res = req.execute()
            for item in res['items']:
                handle_cmd(item['authorDetails'], item['snippet']['displayMessage'])
            time.sleep(5)
        except Exception as e:
            print(f"💀 [BOT] خطأ: {e}")
            db['live_chat_id'] = None
            time.sleep(15)

def run_bot():
    print("🚀 [BOT] بدا الـ Thread تاع البوت")
    if not TOKEN_JSON: return print("💀 [BOT] TOKEN_JSON مكاش")
    try:
        start_youtube_stream()
        time.sleep(20) # خلي البث يطلع
        send_msg(f"{BOT_NAME} طلع 24/7 🚫💸")
    except Exception as e:
        print(f"💀 [STREAM] فشل: {e}")
    print("🤖 [BOT] Credentials صحاح")
    listen_chat()

@app.route('/')
def home(): return f"{BOT_NAME} حي"
@app.route('/ping')
def ping(): return "pong"

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
