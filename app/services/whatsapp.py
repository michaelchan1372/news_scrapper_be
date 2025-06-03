import os
import requests


META_TOKEN = os.getenv('META_TOKEN')

def send_reply(phone_number: str, reply_text: str):
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": reply_text}
    }
    url = f"https://graph.facebook.com/v18.0/{os.getenv('PHONE_NUMBER_ID')}/messages"

    response = httpx.post(url, json=payload, headers=headers)
    print("Reply sent:", response.status_code, response.text)