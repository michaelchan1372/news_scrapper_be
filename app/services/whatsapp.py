import os
import requests


META_TOKEN = os.getenv('META_TOKEN')

def send_reply(phone_number: str, reply_text: str):
    url = f"https://graph.facebook.com/v18.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": reply_text
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Reply status:", response.status_code)
    print("Reply response:", response.text)