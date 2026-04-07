from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "12345"

@app.route('/')
def home():
    return "OK"

@app.route('/webhook', methods=['GET'])
def webhook():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Error"
