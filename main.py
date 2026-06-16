import pytchat, asyncio, json, os
from web import keep_alive
from games import GameEngine
from database import Database
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class InfinityGen:
    def __init__(self):
        self.db = Database()
        self.youtube = self.init_youtube_api()
        self.games = GameEngine(self.db, self.send, self.get_display_name, self.find_user)
        self.live_chat_id = None
        self.chat_users = {}
        self.last_treasure = datetime.now() - timedelta(hours=1)
        self.treasure_active = 0
        print("INFINITY GEN V10.3 شاعل - Teen 13+ 👑🛡️")

    def init_youtube_api(self):
        token_str = os.environ.get("TOKEN")
        if not token_str: return None
        token_data = json.loads(token_str)
        creds = Credentials.from_authorized_user_info(token_data)
        if creds.expired and creds.refresh_token: creds.refresh(Request())
        return build('youtube', 'v3', credentials=creds)

    def get_display_name(self, username):
        data = self.db.get_user_data(username)
        if not data: return username
        name = username
        if data[7] == 1: name = f"👑{name}" # vip
        if data[5] > 0: name = f"🛡️x{data[5]}{name}" # shield
        return name

    def find_user(self, text):
        text = text.replace('@','').lower().strip()
        if text in self.chat_users: return self.chat_users[text]
        for u_lower, u_real in self.chat_users.items():
            if text in u_lower: return u_real
        return None

    def find_live_broadcast(self):
        try:
            req = self.youtube.liveBroadcasts().list(part="id", broadcastStatus="active", maxResults=1)
            res = req.execute()
            return res['items'][0]['id'] if res.get('items') else None
        except: return None

    def get_live_chat_id(self, video_id):
        try:
            req = self.youtube.videos().list(part="liveStreamingDetails", id=video_id)
            res = req.execute()
            return res['items'][0]['liveStreamingDetails']['activeLiveChatId']
        except: return None

    async def send(self, message):
        if not self.youtube or not self.live_chat_id:
            print(f"BOT: {message}")
            return
        try:
            self.youtube.liveChatMessages().insert(
                part="snippet",
                body={"snippet": {"liveChatId": self.live_chat_id,
                                  "type": "textMessageEvent",
                                  "textMessageDetails": {"messageText": message}}}
            ).execute()
        except Exception as e: print(f"Send Error: {e}")

    async def handle_msg(self, user, msg):
        self.chat_users[user.lower()] = user
        self.db.add_user(user)
        self.db.add_points(user, 1)
        msg_l = msg.lower().strip()
        display = self.get_display_name(user)

        # اوامر اساسية
        if msg_l == "سلام": await self.send(f"{display} وعليكم السلام يا جلاد 👑")
        elif msg_l == "نقاطي": await self.send(f"{display} نقاطك: {self.db.get_points(user)} 💰")
        elif msg_l == "هيبة":
            data = self.db.get_user_data(user)
            text = f"{display} هيبتك: "
            if data[5] > 0: text += f"{data[5]} درع 🛡️ "
            if data[7] == 1: text += "تاج VIP 👑 "
            if data[5] == 0 and data[7] == 0: text += "بلا شارات 💀"
            await self.send(text)
        elif msg_l == "متجر": await self.send("🏪 متجر: 1.درع 200 | 2.VIP 1000 | اكتب شراء درع")
        elif msg_l == "شراء درع":
            if self.db.get_points(user) >= 200:
                self.db.add_points(user, -200)
                self.db.execute("UPDATE users SET shield=shield+1 WHERE username=?", (user,))
                self.db.commit()
                await self.send(f"🛡️ {self.get_display_name(user)} شرا درع!")
            else: await self.send(f"{display} نقاطك ناقصة")
        # كنز
        elif msg_l == "نهب":
            if self.treasure_active > 0:
                prize = self.treasure_active
                self.treasure_active = 0
                self.db.add_points(user, prize)
                await self.send(f"💰 {display} نهب الكنز! +{prize} نقطة")
        # اي حاجة اخرى = العاب
        else:
            await self.games.handle_game(user, msg_l, msg.split())

    async def auto_start(self):
        while True:
            # كنز كل ساعة
            if datetime.now() - self.last_treasure > timedelta(hours=1):
                self.last_treasure = datetime.now()
                self.treasure_active = random.randint(100, 500)
                await self.send(f"💎 كـــنـــز طـــاح! اول واحد يكتب 'نهب' يدي {self.treasure_active} نقطة")

            video_id = self.find_live_broadcast()
            if video_id:
                self.live_chat_id = self.get_live_chat_id(video_id)
                if self.live_chat_id:
                    await self.send("INFINITY GEN V10.3 دخل الشات 👑🛡️🔥")
                    chat = pytchat.create(video_id=video_id)
                    while chat.is_alive():
                        for c in chat.get().sync_items():
                            await self.handle_msg(c.author.name, c.message)
                        await asyncio.sleep(1)
            await asyncio.sleep(3)

if __name__ == "__main__":
    keep_alive()
    bot = InfinityGen()
    asyncio.run(bot.auto_start())