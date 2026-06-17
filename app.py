import os, asyncio, threading, queue, subprocess, time, requests, json
from flask import Flask, render_template_string
from datetime import datetime
import pytchat
from database import Database
from games import GameEngine
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

app = Flask(__name__)
log_queue = queue.Queue(maxsize=500)
bot_running = False
current_video_id = None
current_live_chat_id = None
creds = None

HTML = """<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><title>INFINITY GEN</title>
<meta http-equiv="refresh" content="2"><style>
body{background:#0d1117;color:#c9d1d9;font-family:monospace;padding:15px;margin:0}
.header{background:#161b22;padding:12px;border-radius:6px;margin-bottom:12px;border:1px solid #30363d}
.status{color:#3fb950;font-weight:bold}
.log{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px;height:80vh;overflow-y:auto}
.line{margin:1px 0;font-size:13px}.time{color:#8b949e}.msg{color:#58a6ff}.error{color:#f85149}.success{color:#3fb950}
</style></head><body><div class="header"><h1>🤖 INFINITY GEN - 24/7</h1>
<p class="status">● {{ 'شغال' if bot else 'يبحث...' }} | البث: {{ vid }}</p>
<p>اللاعبين: {{ users }} | الالعاب: {{ games }} | {{ time }}</p></div>
<div class="log">{% for l in logs %}<div class="line"><span class="time">[{{ l.time }}]</span> <span class="{{ l.type }}">{{ l.msg }}</span></div>{% endfor %}</div>
</body></html>"""

def log(msg, type="msg"):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "type": type}
    if log_queue.full(): log_queue.get()
    log_queue.put(entry)
    print(f"[{entry['time']}] {msg}")

@app.route('/')
def index():
    logs = list(log_queue.queue)
    return render_template_string(HTML, logs=logs[-150:], time=datetime.now().strftime("%H:%M:%S"),
                                  vid=current_video_id or "يبحث...", bot=bot_running,
                                  users=len(bot.chat_users) if bot_running else 0,
                                  games=len(bot.games.active) if bot_running else 0)

def init_oauth():
    global creds
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json: return log("YOUTUBE_TOKEN_JSON ماكاش", "error")
    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        if creds.expired and creds.refresh_token: creds.refresh(Request())
        log("OAuth2 جاهز", "success")
    except Exception as e: log(f"OAuth Error: {e}", "error")

def send_chat_message(text):
    global current_live_chat_id, creds
    if not current_live_chat_id or not creds: return False
    if creds.expired and creds.refresh_token: creds.refresh(Request())
    url = "https://www.googleapis.com/youtube/v3/liveChat/messages?part=snippet"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {"snippet": {"liveChatId": current_live_chat_id, "type": "textMessageEvent", "textMessageDetails": {"messageText": text}}}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=5)
        return r.status_code == 200
    except: return False

class Bot:
    def __init__(self):
        self.db = Database()
        self.chat_users = {}
        self.games = GameEngine(self.db, self.send, self.get_name, self.find_user)
    def get_name(self, u): return self.chat_users.get(u.lower(), u)
    def find_user(self, name):
        n = name.lower()
        for u in self.chat_users:
            if n in u: return u
        return None
    async def send(self, msg):
        log(f"→ {msg}")
        send_chat_message(msg)
    async def handle(self, user, msg, vid):
        self.chat_users[user.lower()] = user
        self.db.add_user(user)
        self.db.add_points(user, 1)
        log(f"{user}: {msg}")
        await self.games.handle_game(user, msg.lower().strip(), msg.split(), vid)
    async def monitor_chat(self, video_id):
        global current_video_id, bot_running, current_live_chat_id
        current_video_id = video_id
        bot_running = True
        api_key = os.environ.get("YOUTUBE_API_KEY")
        try:
            r = requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={api_key}", timeout=5).json()
            current_live_chat_id = r["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
            log(f"LiveChatID: {current_live_chat_id}", "success")
        except: current_live_chat_id = None
        try:
            chat = pytchat.create(video_id=video_id)
            log(f"دخلت شات: {video_id}", "success")
            await self.send("🤖 INFINITY GEN شغال! اكتب سلام")
            while chat.is_alive():
                for c in chat.get().sync_items():
                    await self.handle(c.author.name, c.message, video_id)
                await asyncio.sleep(0.5)
        except Exception as e: log(f"الشات قطع: {e}", "error")
        finally:
            current_video_id = None
            current_live_chat_id = None
            bot_running = False

bot = Bot()

def get_live_video_id():
    channel_id = os.environ.get("CHANNEL_ID")
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not channel_id or not api_key: return None
    try:
        r = requests.get(f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={channel_id}&eventType=live&type=video&key={api_key}", timeout=5).json()
        return r["items"][0]["id"]["videoId"] if r.get("items") else None
    except: return None

def start_stream():
    stream_key = os.environ.get("STREAM_KEY")
    if not stream_key: return log("STREAM_KEY ماكاش", "error")
    cmd = ["ffmpeg","-re","-stream_loop","-1","-i","video.mp4","-c:v","libx264","-preset","ultrafast",
           "-b:v","2500k","-maxrate","2500k","-bufsize","5000k","-pix_fmt","yuv420p","-g","60",
           "-c:a","aac","-b:a","128k","-ar","44100","-f","flv",f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"]
    log("البث شغال", "success")
    subprocess.run(cmd)

def run_bot():
    init_oauth()
    last_vid = None
    while True:
        vid = get_live_video_id()
        if vid and vid!= last_vid:
            log(f"لقيت بث: {vid}", "success")
            last_vid = vid
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try: loop.run_until_complete(bot.monitor_chat(vid))
            except: pass
        elif not vid: last_vid = None
        time.sleep(3)

threading.Thread(target=start_stream, daemon=True).start()
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))