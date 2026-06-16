import sqlite3

class Database:
    def __init__(self):
        self.db = sqlite3.connect('infinity.db', check_same_thread=False)
        self.init_db()

    def init_db(self):
        self.db.execute('''CREATE TABLE IF NOT EXISTS users
                        (username TEXT PRIMARY KEY,
                         points INT DEFAULT 0,
                         inventory TEXT DEFAULT '{}',
                         bank INT DEFAULT 0,
                         last_daily TIMESTAMP,
                         shield INT DEFAULT 0,
                         last_steal TIMESTAMP,
                         vip INT DEFAULT 0)''')
        self.db.commit()

    def add_user(self, username):
        self.db.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        self.db.commit()

    def get_points(self, username):
        return self.db.execute("SELECT points FROM users WHERE username=?",(username,)).fetchone()[0]

    def add_points(self, username, amount):
        self.db.execute("UPDATE users SET points=points+? WHERE username=?", (amount, username))
        self.db.commit()

    def get_user_data(self, username):
        return self.db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

    def execute(self, query, params=()):
        return self.db.execute(query, params)

    def commit(self):
        self.db.commit()