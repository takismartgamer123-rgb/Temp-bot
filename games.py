import random, asyncio, json
from datetime import datetime, timedelta

class GameEngine:
    def __init__(self, db, send_func, get_display_name, find_user_func):
        self.db = db
        self.send = send_func
        self.get_name = get_display_name
        self.find_user = find_user_func
        self.active = {} # {channel: {game, data}}
        self.cooldowns = {} # {username: {command: timestamp}}
        self.quiz_questions = [
            ("عاصمة الجزائر؟", "الجزائر"), ("5+5*2؟", "15"), ("لون السماء؟", "ازرق"),
            ("كم يوم في الاسبوع؟", "7"), ("اكبر كوكب؟", "المشتري"), ("من اخترع المصباح؟", "اديسون")
        ]

    def get_points(self, username):
        return self.db.execute("SELECT points FROM users WHERE username=?",(username,)).fetchone()[0]

    def add_points(self, username, amount):
        self.db.execute("UPDATE users SET points=points+? WHERE username=?", (amount, username))
        self.db.commit()

    def check_cooldown(self, user, cmd, seconds):
        now = datetime.now()
        if user not in self.cooldowns: self.cooldowns[user] = {}
        last = self.cooldowns[user].get(cmd)
        if last and now - last < timedelta(seconds=seconds):
            return int(seconds - (now - last).total_seconds())
        self.cooldowns[user][cmd] = now
        return 0

    async def handle_game(self, user, msg_l, msg_parts):
        display = self.get_name(user)
        points = self.get_points(user)
        channel_active = self.active.get("global", {})

        # === 1. حرب ===
        if msg_l == "حرب":
            self.active["global"] = {"game":"war", "start":user}
            await self.send(f"⚔️ {display} بدا حرب عالمية! اكتب 'هجوم @اسم' | 🛡️ يحميك")

        # === 2. هجوم ===
        elif msg_l.startswith("هجوم "):
            if channel_active.get("game")!= "war": return
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target or target == user: return
            shield = self.db.execute("SELECT shield FROM users WHERE username=?",(target,)).fetchone()[0]
            if shield > 0:
                self.db.execute("UPDATE users SET shield=shield-1 WHERE username=?", (target,))
                self.db.commit()
                await self.send(f"🛡️ {self.get_name(target)} صد هجوم {display}!")
                return
            dmg = random.randint(10, 50)
            self.add_points(target, -dmg)
            await self.send(f"💥 {display} ضرب {self.get_name(target)} بـ {dmg} ضرر!")

        # === 3. سباق ===
        elif msg_l == "سباق":
            if channel_active.get("game")=="race": await self.send("🏁 كاين سباق شغال"); return
            self.active["global"] = {"game":"race", "scores":{}}
            await self.send(f"🏁 {display} بدا سباق! اكتب 'اركض'. اول واحد 100 يربح 500")

        # === 4. اركض ===
        elif msg_l == "اركض":
            if channel_active.get("game")!= "race": return
            if user not in channel_active["scores"]: channel_active["scores"][user] = 0
            add = random.randint(5, 20)
            channel_active["scores"][user] += add
            score = channel_active["scores"][user]
            await self.send(f"🏃 {display} +{add}. مجموعك: {score}/100")
            if score >= 100:
                self.add_points(user, 500)
                del self.active["global"]
                await self.send(f"🏆 {display} ربح السباق! +500 💰")

        # === 5. حجر ورقة مقص ===
        elif msg_l.startswith("خير "):
            choice = msg_parts[1] if len(msg_parts) > 1 else ""
            if choice not in ["حجر","ورقة","مقص"]: return
            bot = random.choice(["حجر","ورقة","مقص"])
            if choice == bot: result, prize = "تعادل 🤝", 0
            elif (choice=="حجر" and bot=="مقص") or (choice=="ورقة" and bot=="حجر") or (choice=="مقص" and bot=="ورقة"):
                result, prize = "ربحت +20 🎉", 20
            else: result, prize = "خسرت 💀", -10
            self.add_points(user, prize)
            await self.send(f"🎮 {display}: {choice} vs {bot} | {result}")

        # === 6. نرد ===
        elif msg_l == "نرد":
            num = random.randint(1,6)
            prize = num * 5
            self.add_points(user, prize)
            await self.send(f"🎲 {display} رمى: {num} | +{prize}")

        # === 7. سلوت ===
        elif msg_l == "سلوت":
            if points < 10: await self.send(f"{display} لازم 10 نقاط"); return
            self.add_points(user, -10)
            slots = [random.choice(["🍒","🍋","💎","7️⃣","👑"]) for _ in range(3)]
            txt = " | ".join(slots)
            if slots[0] == slots[1] == slots[2]:
                prize = 1000 if slots[0]=="👑" else 500 if slots[0]=="7️⃣" else 200
                self.add_points(user, prize)
                await self.send(f"🎰 {display}: {txt} | جاكبوت +{prize} 💰")
            elif slots[0] == slots[1] or slots[1] == slots[2]:
                self.add_points(user, 30)
                await self.send(f"🎰 {display}: {txt} | +30")
            else: await self.send(f"🎰 {display}: {txt} | خسرت")

        # === 8. صيد ===
        elif msg_l == "صيد":
            cd = self.check_cooldown(user, "صيد", 30)
            if cd: await self.send(f"{display} استنى {cd}ث"); return
            fish = random.choice([("🐟 سمكة", 10), ("🐠 ملونة", 25), ("🦈 قرش", 100), ("👢 فردة", 0), ("💀 لا شيء", 0), ("💎 ماسة", 250)])
            self.add_points(user, fish[1])
            await self.send(f"🎣 {display} صاد: {fish[0]} | +{fish[1]}")

        # === 9. كويز ===
        elif msg_l == "كويز":
            if channel_active.get("game")=="quiz": return
            q = random.choice(self.quiz_questions)
            self.active["global"] = {"game":"quiz", "answer":q[1].lower(), "prize":50}
            await self.send(f"🧠 كويز: {q[0]} | اكتب 'جواب...' | +50")

        # === 10. جواب ===
        elif msg_l.startswith("جواب "):
            if channel_active.get("game")!= "quiz": return
            answer = " ".join(msg_parts[1:]).lower()
            if answer == channel_active["answer"]:
                prize = channel_active["prize"]
                self.add_points(user, prize)
                del self.active["global"]
                await self.send(f"✅ {display} جاوب صح! +{prize}")

        # === 11. سرقة ===
        elif msg_l.startswith("سرقة "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target or target == user: return
            cd = self.check_cooldown(user, "سرقة", 300)
            if cd: await self.send(f"{display} استنى {cd//60}د"); return
            shield = self.db.execute("SELECT shield FROM users WHERE username=?",(target,)).fetchone()[0]
            if shield > 0:
                self.db.execute("UPDATE users SET shield=shield-1 WHERE username=?", (target,))
                await self.send(f"🛡️ {self.get_name(target)} صد السرقة!")
            else:
                steal = min(50, self.get_points(target))
                self.add_points(user, steal)
                self.add_points(target, -steal)
                await self.send(f"💰 {display} سرق {steal} من {self.get_name(target)}!")
            self.db.commit()

        # === 12. تحويل ===
        elif msg_l.startswith("تحويل "):
            if len(msg_parts) < 3: return
            target = self.find_user(msg_parts[1])
            try: amount = int(msg_parts[2])
            except: return
            if not target or amount <= 0 or points < amount: return
            self.add_points(user, -amount)
            self.add_points(target, amount)
            await self.send(f"💸 {display} حول {amount} لـ {self.get_name(target)}")

        # === 13. قمار ===
        elif msg_l.startswith("قمار "):
            if len(msg_parts) < 2: return
            try: bet = int(msg_parts[1])
            except: return
            if bet <= 0 or points < bet: return
            if random.random() < 0.48:
                self.add_points(user, bet)
                await self.send(f"🎲 {display} ربح القمار! +{bet}")
            else:
                self.add_points(user, -bet)
                await self.send(f"💀 {display} خسر -{bet}")

        # === 14. عمل ===
        elif msg_l == "عمل":
            cd = self.check_cooldown(user, "عمل", 60)
            if cd: await self.send(f"{display} استنى {cd}ث"); return
            earn = random.randint(20, 100)
            self.add_points(user, earn)
            job = random.choice(["بعت تمور","بريكوليت","طورت بوت","نضفت","ستريمت"])
            await self.send(f"💼 {display} {job} +{earn}")

        # === 15. صندوق ===
        elif msg_l == "صندوق":
            if points < 50: return
            self.add_points(user, -50)
            loot = random.choices([("🛡️ درع", "shield", 1), ("💰 200 نقطة", "points", 200), ("👑 VIP", "vip", 1), ("💀 لا شيء", "points", 0)], weights=[40,40,5,15])[0]
            if loot[1] == "shield": self.db.execute("UPDATE users SET shield=shield+1 WHERE username=?", (user,))
            elif loot[1] == "vip": self.db.execute("UPDATE users SET vip=1 WHERE username=?", (user,))
            else: self.add_points(user, loot[2])
            self.db.commit()
            await self.send(f"📦 {display} فتح و لقى: {loot[0]}")

        # === 16. زهر ===
        elif msg_l == "زهر":
            num = random.randint(1,100)
            if num == 100: prize = 1000; txt = "جاكبوت اسطوري"
            elif num > 90: prize = 200; txt = "محظوظ"
            elif num > 50: prize = 20; txt = "عادي"
            else: prize = 0; txt = "نحس"
            self.add_points(user, prize)
            await self.send(f"🍀 {display} زهرك: {num}/100 {txt} +{prize}")

        # === 17. روليت ===
        elif msg_l.startswith("روليت "):
            if len(msg_parts) < 3: return
            try: bet = int(msg_parts[2])
            except: return
            if bet <= 0 or points < bet: return
            color = msg_parts[1]
            if color not in ["احمر","اسود","اخضر"]: return
            result = random.choice(["احمر","اسود","احمر","اسود","اخضر"])
            if color == result:
                prize = bet * 14 if color == "اخضر" else bet * 2
                self.add_points(user, prize - bet)
                await self.send(f"🎡 {display} روليت: {result} | ربحت +{prize-bet}")
            else:
                self.add_points(user, -bet)
                await self.send(f"🎡 {display} روليت: {result} | خسرت -{bet}")

        # === 18. هروب ===
        elif msg_l == "هروب":
            if random.random() < 0.3:
                self.add_points(user, 100)
                await self.send(f"🏃 {display} هرب من الشرطة +100")
            else:
                self.add_points(user, -50)
                await self.send(f"🚔 {display} قبضوه -50")

        # === 19. استثمار ===
        elif msg_l.startswith("استثمار "):
            if len(msg_parts) < 2: return
            try: amount = int(msg_parts[1])
            except: return
            if amount <= 0 or points < amount: return
            self.add_points(user, -amount)
            await self.send(f"📈 {display} استثمر {amount}. ارجع بعد 10د و اكتب 'سحب'")
            self.active[user] = {"game":"invest", "amount":amount, "time":datetime.now()}

        # === 20. سحب ===
        elif msg_l == "سحب":
            data = self.active.get(user)
            if not data or data.get("game")!= "invest": return
            if datetime.now() - data["time"] < timedelta(minutes=10):
                await self.send(f"{display} مازال ما طابش الاستثمار"); return
            profit = int(data["amount"] * random.uniform(0.5, 2.0))
            self.add_points(user, data["amount"] + profit)
            del self.active[user]
            await self.send(f"💰 {display} سحب الاستثمار: {data['amount']} + ربح {profit}")

        # === 21. زواج ===
        elif msg_l.startswith("زواج "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target or target == user: return
            if points < 500: await self.send(f"{display} الزواج بـ 500 نقطة"); return
            self.add_points(user, -500)
            await self.send(f"💍 {display} طلب يد {self.get_name(target)} للزواج! {self.get_name(target)} اكتب 'قبول' او 'رفض'")
            self.active["global"] = {"game":"marriage", "from":user, "to":target}

        # === 22. قبول ===
        elif msg_l == "قبول":
            if channel_active.get("game")!= "marriage" or channel_active.get("to")!= user: return
            await self.send(f"💒 {self.get_name(channel_active['from'])} و {display} تزوجو! مبروك +1000 لكل واحد")
            self.add_points(channel_active['from'], 1000)
            self.add_points(user, 1000)
            del self.active["global"]

        # === 23. طلاق ===
        elif msg_l == "طلاق":
            if points < 1000: await self.send(f"{display} الطلاق بـ 1000 نقطة"); return
            self.add_points(user, -1000)
            await self.send(f"💔 {display} تطلق و خسر 1000 نقطة. الحرية لها ثمن")

        # === 24. هدية ===
        elif msg_l.startswith("هدية "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target: return
            gift = random.choice([("🌹 وردة", 10), ("🍫 شوكولا", 20), ("💎 ماسة", 100), ("💀 قنبلة", -50)])
            self.add_points(target, gift[1])
            await self.send(f"🎁 {display} اهدى {self.get_name(target)}: {gift[0]} | {gift[1]} نقطة")

        # === 25. ملك ===
        elif msg_l == "ملك":
            if points < 5000: await self.send(f"{display} لازم 5000 نقطة باه تولي ملك"); return
            self.add_points(user, -5000)
            self.db.execute("UPDATE users SET vip=1 WHERE username=?", (user,))
            self.db.commit()
            await self.send(f"👑 {display} شرا التاج و ولا ملك الشات!")

        # === 26. دعاء ===
        elif msg_l == "دعاء":
            duas = ["الله يرزقك","الله يحفظك","موفق","الله يفتح عليك"]
            await self.send(f"🤲 {display} {random.choice(duas)} +5 حسنات +5 نقاط")
            self.add_points(user, 5)

        # === 27. طرد ===
        elif msg_l.startswith("طرد "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target: return
            if points < 200: return
            self.add_points(user, -200)
            await self.send(f"👢 {display} طرد {self.get_name(target)} من اللعبة! -200")

        # === 28. حماية ===
        elif msg_l == "حماية":
            if points < 100: return
            self.add_points(user, -100)
            self.db.execute("UPDATE users SET shield=shield+1 WHERE username=?", (user,))
            self.db.commit()
            await self.send(f"🔰 {display} فعل حماية +1 درع")

        # === 29. سم ===
        elif msg_l.startswith("سم "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target or points < 50: return
            self.add_points(user, -50)
            self.add_points(target, -30)
            await self.send(f"☠️ {display} سمم {self.get_name(target)} -30")

        # === 30. علاج ===
        elif msg_l == "علاج":
            if points < 30: return
            self.add_points(user, -30)
            await self.send(f"💊 {display} تعالج +20 نقطة")
            self.add_points(user, 20)

        # === 31. كنز مخفي ===
        elif msg_l == "احفر":
            cd = self.check_cooldown(user, "احفر", 120)
            if cd: return
            find = random.random()
            if find < 0.1: prize, txt = 300, "كنز ذهب"
            elif find < 0.3: prize, txt = 100, "جرة نقود"
            elif find < 0.6: prize, txt = 30, "قطع نقدية"
            else: prize, txt = 0, "لا شيء"
            self.add_points(user, prize)
            await self.send(f"⛏️ {display} حفر و لقى: {txt} +{prize}")

        # === 32. سجن ===
        elif msg_l.startswith("سجن "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target or points < 150: return
            self.add_points(user, -150)
            await self.send(f"⛓️ {display} سجن {self.get_name(target)} لمدة 2د! ما يقدرش يلعب")
            self.active[target] = {"game":"jail", "until":datetime.now() + timedelta(minutes=2)}

        # === 33. افحص سجن ===
        if user in self.active and self.active[user].get("game")=="jail":
            if datetime.now() < self.active[user]["until"]:
                await self.send(f"⛓️ {display} مازلت في السجن"); return
            else: del self.active[user]

        # === 34. تحدي ===
        elif msg_l.startswith("تحدي "):
            if len(msg_parts) < 3: return
            target = self.find_user(msg_parts[1])
            try: bet = int(msg_parts[2])
            except: return
            if not target or bet <= 0 or points < bet or self.get_points(target) < bet: return
            await self.send(f"⚔️ {display} تحدى {self.get_name(target)} على {bet} نقطة! {self.get_name(target)} اكتب 'قبل التحدي'")
            self.active["global"] = {"game":"duel", "p1":user, "p2":target, "bet":bet}

        # === 35. قبل التحدي ===
        elif msg_l == "قبل التحدي":
            if channel_active.get("game")!= "duel" or channel_active.get("p2")!= user: return
            p1, p2, bet = channel_active["p1"], channel_active["p2"], channel_active["bet"]
            winner = random.choice([p1, p2])
            loser = p2 if winner == p1 else p1
            self.add_points(winner, bet)
            self.add_points(loser, -bet)
            del self.active["global"]
            await self.send(f"🏆 {self.get_name(winner)} ربح التحدي ضد {self.get_name(loser)}! +{bet}")

        # === 36. يانصيب ===
        elif msg_l == "يانصيب":
            if points < 20: return
            self.add_points(user, -20)
            if random.random() < 0.05:
                self.add_points(user, 1000)
                await self.send(f"🎟️ {display} ربح اليانصيب! +1000 💰💰💰")
            else: await self.send(f"🎟️ {display} خسر اليانصيب")

        # === 37. بنك ===
        elif msg_l.startswith("بنك "):
            if len(msg_parts) < 2: return
            try: amount = int(msg_parts[1])
            except: return
            if amount <= 0 or points < amount: return
            self.add_points(user, -amount)
            self.db.execute("UPDATE users SET bank=bank+? WHERE username=?", (amount, user))
            self.db.commit()
            await self.send(f"🏦 {display} ودع {amount} في البنك")

        # === 38. سحب بنك ===
        elif msg_l.startswith("سحب بنك "):
            if len(msg_parts) < 2: return
            try: amount = int(msg_parts[1])
            except: return
            bank = self.db.execute("SELECT bank FROM users WHERE username=?",(user,)).fetchone()[0]
            if amount <= 0 or bank < amount: return
            self.db.execute("UPDATE users SET bank=bank-? WHERE username=?", (amount, user))
            self.add_points(user, amount)
            self.db.commit()
            await self.send(f"🏦 {display} سحب {amount} من البنك")

        # === 39. فوائد ===
        elif msg_l == "فوائد":
            bank = self.db.execute("SELECT bank FROM users WHERE username=?",(user,)).fetchone()[0]
            if bank == 0: await self.send(f"{display} ما عندكش فلوس في البنك"); return
            profit = int(bank * 0.05)
            self.db.execute("UPDATE users SET bank=bank+? WHERE username=?", (profit, user))
            self.db.commit()
            await self.send(f"📈 {display} فوائد البنك: +{profit} | رصيدك: {bank+profit}")

        # === 40. شراء vip ===
        elif msg_l == "شراء vip":
            if points < 1000: await self.send(f"{display} VIP بـ 1000 نقطة"); return
            self.add_points(user, -1000)
            self.db.execute("UPDATE users SET vip=1 WHERE username=?", (user,))
            self.db.commit()
            await self.send(f"👑 {display} ولا VIP! اسمك ضرك ذهبي")

        # === 41. شتم ===
        elif msg_l.startswith("شتم "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target: return
            roasts = ["بطاطا","نوب","ما تعرفش تلعب","حظك نحس"]
            await self.send(f"🤬 {display} شتم {self.get_name(target)}: يا {random.choice(roasts)}")

        # === 42. مدح ===
        elif msg_l.startswith("مدح "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target: return
            comps = ["اسطورة","جلاد","ملك اللعبة","محظوظ"]
            self.add_points(target, 10)
            await self.send(f"😇 {display} مدح {self.get_name(target)}: انت {random.choice(comps)} +10")

        # === 43. قتل ===
        elif msg_l.startswith("قتل "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target: return
            if random.random() < 0.2:
                self.add_points(target, -100)
                await self.send(f"🔪 {display} قتل {self.get_name(target)}! -100")
            else: await self.send(f"🛡️ {self.get_name(target)} تفادى القتل")

        # === 44. احياء ===
        elif msg_l.startswith("احياء "):
            if len(msg_parts) < 2: return
            target = self.find_user(msg_parts[1])
            if not target or points < 50: return
            self.add_points(user, -50)
            self.add_points(target, 100)
            await self.send(f"✨ {display} احيا {self.get_name(target)} +100")

        # === 45. قنبلة ===
        elif msg_l == "قنبلة":
            if points < 300: return
            self.add_points(user, -300)
            await self.send(f"💣 {display} فجر قنبلة! كل واحد خسر 20 نقطة عشوائي")
            # ننقص من 5 عشوائيين

        # === 46. درع جماعي ===
        elif msg_l == "درع جماعي":
            if points < 500: return
            self.add_points(user, -500)
            await self.send(f"🛡️ {display} فعل درع جماعي! الكل محمي 5د")
            self.active["global"] = {"game":"global_shield", "until":datetime.now() + timedelta(minutes=5)}

        # === 47. يومي ===
        elif msg_l == "يومي":
            last = self.db.execute("SELECT last_daily FROM users WHERE username=?",(user,)).fetchone()[0]
            if last and datetime.now() - datetime.fromisoformat(last) < timedelta(hours=24):
                await self.send(f"{display} خذيت اليومي. ارجع غدا"); return
            prize = random.randint(100, 300)
            self.add_points(user, prize)
            self.db.execute("UPDATE users SET last_daily=? WHERE username=?", (datetime.now(), user))
            self.db.commit()
            await self.send(f"🎁 {display} مكافأة يومية: +{prize}")

        # === 48. رانك ===
        elif msg_l == "رانك":
            if points > 10000: rank = "👑 اسطوري"
            elif points > 5000: rank = "💎 ماسي"
            elif points > 2000: rank = "🥇 ذهبي"
            elif points > 1000: rank = "🥈 فضي"
            elif points > 500: rank = "🥉 برونزي"
            else: rank = "🌱 مبتدئ"
            await self.send(f"🎖️ {display} رانكك: {rank} | نقاطك: {points}")

        # === 49. بوس ===
        elif msg_l == "بوس":
            if channel_active.get("game")=="boss": await self.send("🐉 كاين بوس ضرك"); return
            self.active["global"] = {"game":"boss", "hp":1000}
            await self.send(f"🐉 {display} استدعى بوس! HP: 1000 | اكتب 'ضرب' تنقص من دمو. اللي يقتله +1000")

        # === 50. ضرب ===
        elif msg_l == "ضرب":
            if channel_active.get("game")!= "boss": return
            dmg = random.randint(20, 100)
            channel_active["hp"] -= dmg
            await self.send(f"⚔️ {display} ضرب البوس -{dmg} | HP باقي: {channel_active['hp']}")
            if channel_active["hp"] <= 0:
                self.add_points(user, 1000)
                del self.active["global"]
                await self.send(f"🏆 {display} قتل البوس! +1000 نقطة 💰")