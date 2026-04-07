from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "mytoken123"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403

    if request.method == "POST":
        print("📩 Data:", request.json)
        return "EVENT_RECEIVED", 200

    return "OK", 200
