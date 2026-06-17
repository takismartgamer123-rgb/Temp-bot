import sqlite3
class Database:
    def __init__(self):
        self.db = "bot.db"
        self.init()
    def init(self):
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, points INTEGER DEFAULT 100)")
            c.execute("CREATE TABLE IF NOT EXISTS items (username TEXT, item TEXT)")
    def add_user(self, u):
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT OR IGNORE INTO users VALUES (?,100)", (u.lower(),))
    def add_points(self, u, p):
        self.add_user(u)
        with sqlite3.connect(self.db) as c:
            c.execute("UPDATE users SET points=points+? WHERE username=?", (p, u.lower()))
    def get_points(self, u):
        with sqlite3.connect(self.db) as c:
            r = c.execute("SELECT points FROM users WHERE username=?", (u.lower(),)).fetchone()
            return r[0] if r else 0
    def add_item(self, u, i):
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT INTO items VALUES (?,?)", (u.lower(), i))
    def get_items(self, u):
        with sqlite3.connect(self.db) as c:
            return [x[0] for x in c.execute("SELECT item FROM items WHERE username=?", (u.lower(),)).fetchall()]