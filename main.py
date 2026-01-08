from flask import Flask
from threading import Thread
from bot import start_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Serena Lec Bot is Running!"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "Serena Lec"}

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    start_bot()
