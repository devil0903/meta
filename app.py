import os
import json
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "12345")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

client = genai.Client(api_key=GEMINI_KEY)

conversation_history = {}

SYSTEM_PROMPT = """You are a helpful WhatsApp appointment booking assistant for a medical clinic in Prayagraj, India.

Your job:
- Help patients book, reschedule or cancel appointments
- Answer questions about clinic timings, doctors, and fees
- Respond naturally in the same language the patient uses (Hindi, English, or Hinglish)
- Be warm, polite and professional like a good receptionist
- Keep replies short and clear — this is WhatsApp, not email
- Never reply with long paragraphs — use short lines with line breaks
- Never use markdown like ** or ## — plain text only

Clinic details:
- Name: Sharma Clinic
- Doctors: Dr. Amit Sharma (General), Dr. Priya Singh (Gynaecology), Dr. Rakesh Gupta (Ortho)
- Timings: Mon-Sat 9AM-1PM and 4PM-8PM, Sunday 10AM-1PM
- Consultation fee: Rs. 300 (General), Rs. 500 (Gynaecology), Rs. 400 (Ortho)
- Address: 14 Civil Lines, Prayagraj
- No advance payment required

When booking appointment always collect:
1. Patient name
2. Doctor preference
3. Preferred date and time

After collecting all details confirm like this:
Appointment confirm ho gayi!
Patient: [name]
Doctor: [doctor name]
Date: [date]
Time: [time]
Jagah: 14 Civil Lines, Prayagraj

Available slots:
Morning: 9:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30
Evening: 4:00, 4:30, 5:00, 5:30, 6:00, 6:30, 7:00, 7:30

If patient asks something you cannot handle say:
Iske liye clinic pe call karein: 9876543210
"""

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

def get_ai_reply(user_number, user_message):
    if user_number not in conversation_history:
        conversation_history[user_number] = []

    conversation_history[user_number].append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )
    )

    if len(conversation_history[user_number]) > 20:
        conversation_history[user_number] = conversation_history[user_number][-20:]

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=500,
            temperature=0.7,
        ),
        contents=conversation_history[user_number]
    )

    ai_reply = response.text

    conversation_history[user_number].append(
        types.Content(
            role="model",
            parts=[types.Part(text=ai_reply)]
        )
    )

    return ai_reply

@app.route('/')
def home():
    return "ClinicBot is running!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified!")
        return challenge
    return "Error", 403

@app.route('/webhook', methods=['POST'])
def receive_message():
    try:
        data = request.get_json()
        print("Incoming data:", json.dumps(data, indent=2))

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
            print(f"Message from {from_number}: {user_text}")

            ai_reply = get_ai_reply(from_number, user_text)
            print(f"AI reply: {ai_reply}")

            send_whatsapp_message(from_number, ai_reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
