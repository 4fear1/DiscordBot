from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Bot Status</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    background: rgba(0,0,0,0.3);
                    padding: 40px;
                    border-radius: 15px;
                }
                h1 { font-size: 3em; margin: 0; }
                p { font-size: 1.5em; }
                .status { color: #00ff00; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Bot Discord</h1>
                <p class="status">✅ ONLINE E FUNCIONANDO!</p>
                <p>Hextech Matchmaking System ativo</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "ok", "bot": "online"}, 200

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    """Inicia o servidor Flask em uma thread separada"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print(f"🌐 Keep-alive server iniciado na porta {os.environ.get('PORT', 8080)}")