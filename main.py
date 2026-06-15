import subprocess, threading, os, time, json, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 1. نخزن النقاط في ملف json بسيط
POINTS_FILE = 'points.json'
def load_points():
    try:
        with open(POINTS_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_points(data):
    with open(POINTS_FILE, 'w') as f: json.dump(data, f)

def add_points(user_id, amount):
    data = load_points()
    data[user_id] = data.get(user_id, 0) + amount
    save_points(data)
    return data[user_id]

def get_points(user_id):
    return load_points().get(user_id, 0)

# 2. البث تاع video.mp4
def start_stream():
    stream_key = os.environ.get('YT_STREAM_KEY')
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    cmd = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', 'video.mp4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '300k',
           '-s', '854x480', '-c:a', 'aac', '-b:a', '32k', '-f', 'flv', rtmp_url]
    print("📺 [STREAM] بدا البث 480p 🚫💸")
    while True:
        subprocess.run(cmd)
        time.sleep(5)

# 3. البوت تاع الشات
def start_bot():
    print("🤖 [BOT] بديت نعس على البث...")

    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get('TOKEN_JSON')))
    youtube = build('youtube', 'v3', credentials=creds)

    live_chat_id = None

    # 1. لوب يعس حتى يلقى البث
    while not live_chat_id:
        try:
            broadcasts = youtube.liveBroadcasts().list(
                part="snippet",
                broadcastStatus="active"
            ).execute()

            if broadcasts['items']:
                live_chat_id = broadcasts['items'][0]['snippet']['liveChatId']
                print(f"✅ [BOT] لقيت البث! liveChatId: {live_chat_id}")
            else:
                print("⏳ [BOT] مزال ما طلعش البث... نعاود بعد 3 ثواني")
                time.sleep(3)

        except Exception as e:
            print(f"💀 [BOT] خطأ في البحث عن البث: {e}")
            time.sleep(10)

    # 2. كي يلقاه يبدا يقرا الشات
    print("🤖 [BOT] بديت نقرا في الشات 🚫💸")

    def send_msg(text):
        try:
            youtube.liveChatMessages().insert(part="snippet", body={
                "snippet": {"liveChatId": live_chat_id, "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text}}
            }).execute()
        except Exception as e: print(f"💀 [BOT] ما قدرتش نبعث: {e}")

    next_page_token = None
    while True:
        try:
            response = youtube.liveChatMessages().list(
                liveChatId=live_chat_id, part="snippet,authorDetails", pageToken=next_page_token
            ).execute()

            for item in response['items']:
                msg = item['snippet']['displayMessage'].strip()
                author = item['authorDetails']['displayName']
                author_id = item['authorDetails']['channelId']

                new_total = add_points(author_id, 1)

                if msg.lower() == '!سلام':
                    send_msg(f"وعليكم السلام @{author} 🚫💸")
                elif msg.lower() == '!نقاطي':
                    points = get_points(author_id)
                    send_msg(f"@{author} عندك {points} نقطة 🚫💸")
                elif msg.lower() == '!بنق':
                    send_msg(f"Pong! البوت حي 🚫💸")
                elif msg.lower() == '!حظ':
                    if random.random() > 0.4:
                        add_points(author_id, 5)
                        send_msg(f"@{author} ربحت 5 نقاط! مجموعك {get_points(author_id)} 🚫💸")
                    else:
                        send_msg(f"@{author} خسرت 😭 جرب مرة أخرى")
                elif msg.lower() == '!توب':
                    data = load_points()
                    top = sorted(data.items(), key=lambda x: x[1], reverse=True)[:3]
                    msg_top = "🏆 توب 3: "
                    for i, (uid, pts) in enumerate(top): msg_top += f"{i+1}- {pts}ن | "
                    send_msg(msg_top + "🚫💸")

            next_page_token = response.get('nextPageToken')
            time.sleep(5)
        except Exception as e:
            print(f"💀 [BOT] Error في الشات: {e}")
            time.sleep(15)
