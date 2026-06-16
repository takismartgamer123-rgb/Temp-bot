from flask import Flask
from threading import Thread
from stream import start_stream
import os

app = Flask('')

@app.route('/')
def home(): 
    return "INFINITY GEN V10.3 شاعل 👑🔥🛡️"

@app.route('/health')
def health(): 
    return "OK", 200

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # شغل Flask في Thread
    t = Thread(target=run)
    t.daemon = True
    t.start()
    
    # شغل البث في Thread ثاني
    t2 = Thread(target=start_stream)
    t2.daemon = True
    t2.start()