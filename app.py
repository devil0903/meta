from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "mytoken123"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print("🔥 Request received")
    print("Method:", request.method)
    print("Args:", request.args)

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    if request.method == "POST":
        print("📩 Data:", request.json)
        return "EVENT_RECEIVED", 200

    return "OK", 200
