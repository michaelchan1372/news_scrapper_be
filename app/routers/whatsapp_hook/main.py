import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from starlette import status
from pydantic import BaseModel, Field

VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

router = APIRouter(
    prefix='/webhook',
    tags=['webhook']
)


@router.get("/hook", status_code=status.HTTP_200_OK)
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return PlainTextResponse(content="Forbidden", status_code=403)

@router.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    print("Incoming webhook:", body)

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages")

        if messages:
            msg = messages[0]
            phone = msg["from"]
            text = msg["text"]["body"]
            print(f"Message from {phone}: {text}")

            # You can call the Cloud API here to reply (e.g., using httpx or requests)

    except Exception as e:
        print("Error handling message:", e)

    return {"status": "received"}