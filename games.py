import random, asyncio
from datetime import datetime, timedelta

class GameEngine:
    def __init__(self, db, send_func, get_name, find_user):
        self.db = db
        self.send = send_func
        self.get_name = get_name
        self.find_user = find_user
        self.active = {} # {video_id: {game, data}}
        self.cooldowns = {} # {user: {cmd: time}}
        self.shop = {
            "درع": 200, "مضاعف": 500, "كشف": 150, "قنبلة": 400, "كاتم": 600,
            "شرطي": 500, "انعاش": 700, "تصويت_ذهبي": 350, "جاسوس": 800, "انتحاري": 1000
        }
    
    def get_points(self, u):
        row = self.db.execute("SELECT points FROM users WHERE username=?", (u,)).fetchone()
        return row[0] if row else 0
    
    def add_points(self, u, n):
        self.db.execute("UPDATE users SET points=points+? WHERE username=?", (n, u))
        self.db.commit()
    
    def cd(self, u, cmd, sec):
        now = datetime.now()
        if u not in self.cooldowns: self.cooldowns[u] = {}
        last = self.cooldowns[u].get(cmd)
        if last and now - last < timedelta(seconds=sec):
            return int(sec - (now - last).total_seconds())
        self.cooldowns[u][cmd] = now
        return 0
    
    async def handle_game(self, user, msg_l, msg_parts, vid):
        display = self.get_name(user)
        points = self.get_points(user)
        ch = self.active.get(vid, {})
        
        # اوامر اساسية
        if msg_l == "سلام": await self.send(f"👋 وعليكم السلام {display}")
        elif msg_l == "نقاطي": await self.send(f"💰 {display} نقاطك: {points}")
        elif msg_l == "توب":
            top = self.db.execute("SELECT username,points FROM users ORDER BY points DESC LIMIT 10").fetchall()
            txt = "🏆 توب 10:\n" + "\n".join([f"{i+1}. {u} - {p}" for i,u,p in enumerate(top)])
            await self.send(txt)
        elif msg_l == "بنق": await self.send(f"📶 بنق البوت: 20ms")
        elif msg_l == "متجر":
            txt = "🛒 المتجر:\n" + "\n".join([f"{k} = {v}" for k,v in self.shop.items()])
            await self.send(txt)
        
        # شراء من المتجر
        elif msg_l.startswith("شراء "):
            item = " ".join(msg_parts[1:])
            if item in self.shop:
                price = self.shop[item]
                if points >= price:
                    self.add_points(user, -price)
                    self.db.execute("UPDATE users SET inventory=inventory||?||',' WHERE username=?", (item, user))
                    self.db.commit()
                    await self.send(f"✅ {display} شرا {item} بـ {price}")
                else: await self.send(f"❌ {display} ماعندكش نقاط كافية")
        
        # الالعاب 1-8
        elif msg_l == "xo start":
            if ch.get("game"): return
            self.active[vid] = {"game": "xo", "board": ["1","2","3","4","5","6","7","8","9"], "turn": "X", "p1": user, "p2": None}
            await self.send(f"⭕❌ {display} بدا XO! اكتب 'ادخل' للدخول")
        elif msg_l == "ادخل":
            if ch.get("game") == "xo" and not ch["p2"] and user!= ch["p1"]:
                ch["p2"] = user
                await self.send(f"⭕ {display} دخل! X يبدا: 'لعب 5'")
        elif msg_l.startswith("لعب "):
            if ch.get("game")!= "xo": return
            try: pos = int(msg_parts[1]) - 1
            except: return
            current = ch["p1"] if ch["turn"] == "X" else ch["p2"]
            if user!= current or pos < 0 or pos > 8 or ch["board"][pos] in ["❌","⭕"]: return
            ch["board"][pos] = "❌" if ch["turn"] == "X" else "⭕"
            wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
            b, s = ch["board"], ch["board"][pos]
            if any(b[a]==b[b]==b[c]==s for a,b,c in wins):
                self.add_points(user, 100)
                await self.send(f"🏆 {display} ربح XO! +100")
                del self.active[vid]
            else:
                ch["turn"] = "O" if ch["turn"] == "X" else "X"
                grid = f"{b[0]}{b[1]}{b[2]}\n{b[3]}{b[4]}{b[5]}\n{b[6]}{b[7]}{b[8]}"
                await self.send(f"{grid}\nدور {ch['turn']}")
        
        elif msg_l == "rps start":
            c = random.choice(["حجر","ورقة","مقص"])
            self.active[vid] = {"game": "rps", "bot": c}
            await self.send(f"✂️ حجر ورقة مقص! اكتب: حجر / ورقة / مقص")
        elif msg_l in ["حجر","ورقة","مقص"] and ch.get("game") == "rps":
            bot = ch["bot"]
            if msg_l == bot: res, p = "تعادل", 0
            elif (msg_l=="حجر" and bot=="مقص") or (msg_l=="ورقة" and bot=="حجر") or (msg_l=="مقص" and bot=="ورقة"):
                res, p = "ربحت", 20
            else: res, p = "خسرت", -10
            self.add_points(user, p)
            await self.send(f"🎮 {display}: {msg_l} vs {bot} | {res} {p}")
            del self.active[vid]
        
        elif msg_l == "تخمين start":
            self.active[vid] = {"game": "guess", "num": random.randint(1,100)}
            await self.send(f"🎯 خمنت رقم 1-100 | اكتب 'رقم 50'")
        elif msg_l.startswith("رقم ") and ch.get("game") == "guess":
            try: g = int(msg_parts[1])
            except: return
            t = ch["num"]
            if g == t:
                self.add_points(user, 100)
                await self.send(f"🎉 {display} جابو {t}! +100")
                del self.active[vid]
            elif g < t: await self.send(f"📈 اكبر من {g}")
            else: await self.send(f"📉 اصغر من {g}")
        
        # الالعاب 9-16 مبسطة
        elif msg_l == "كلمات start":
            words = ["برمجة","يوتيوب","الجزائر","رمضان","قهوة"]
            w = random.choice(words)
            self.active[vid] = {"game": "word", "word": w}
            await self.send(f"⌨️ اكتب كلمة '{w}' باسرع وقت! +60")
        elif msg_l == self.active.get(vid,{}).get("word"):
            self.add_points(user, 60)
            await self.send(f"⚡ {display} كتبها صح! +60")
            del self.active[vid]
        
        elif msg_l == "مليون start":
            self.active[vid] = {"game": "million", "q": "عاصمة الجزائر؟", "a": "الجزائر"}
            await self.send(f"💰 من سيربح النقاط: عاصمة الجزائر؟")
        elif msg_l == "الجزائر" and ch.get("game") == "million":
            self.add_points(user, 200)
            await self.send(f"🎉 {display} صحيح! +200")
            del self.active[vid]