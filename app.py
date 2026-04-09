import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "12345")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# Store conversation state
user_state = {}

def send_whatsapp_message(to_number, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("WhatsApp send status:", response.status_code, response.text)
    return response

def get_reply(user_number, user_text):
    text = user_text.lower()

    # Initialize user state
    if user_number not in user_state:
        user_state[user_number] = {"step": None}

    state = user_state[user_number]

    # Booking flow
    if state["step"] == "ask_name":
        state["name"] = user_text
        state["step"] = "ask_doctor"
        return "Kaunse doctor ke liye appointment chahiye?\n1. Dr Amit (General)\n2. Dr Priya (Gynae)\n3. Dr Rakesh (Ortho)"

    elif state["step"] == "ask_doctor":
        state["doctor"] = user_text
        state["step"] = "ask_time"
        return "Kis date aur time pe aana chahenge?\nExample: 12 April 10:30"

    elif state["step"] == "ask_time":
        state["time"] = user_text
        state["step"] = None

       return f"""Appointment confirm ho gayi!

Patient: {state.get('name')}
Doctor: {state.get('doctor')}
Date/Time: {state.get('time')}

Jagah: 14 Civil Lines, Prayagraj"""
    # General queries (FREE logic)
    if "time" in text or "timing" in text:
        return "Clinic timing:\nMon-Sat 9-1 & 4-8\nSunday 10-1"

    elif "fee" in text or "charge" in text:
        return "Fees:\nGeneral: 300\nGynae: 500\nOrtho: 400"

    elif "doctor" in text:
        return "Doctors:\nDr Amit (General)\nDr Priya (Gynae)\nDr Rakesh (Ortho)"

    elif "address" in text or "location" in text:
        return "14 Civil Lines, Prayagraj"

    elif "appointment" in text or "book" in text:
        state["step"] = "ask_name"
        return "Appointment book karne ke liye apna naam bataiye"

    else:
        return "Samajh nahi aaya.\nCall karein: 9876543210"

@app.route('/')
def home():
    return "ClinicBot running!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge
    return "Error", 403

@app.route('/webhook', methods=['POST'])
def receive_message():
    try:
        data = request.get_json()
        print("Incoming:", json.dumps(data, indent=2))

        entry = data.get("entry", [])
        if not entry:
            return jsonify({"status": "ok"}), 200

        changes = entry[0].get("changes", [])
        if not changes:
            return jsonify({"status": "ok"}), 200

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return jsonify({"status": "ok"}), 200

        message = messages[0]
        from_number = message.get("from")
        msg_type = message.get("type")

        if msg_type == "text":
            user_text = message["text"]["body"]
            reply = get_reply(from_number, user_text)
            send_whatsapp_message(from_number, reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
