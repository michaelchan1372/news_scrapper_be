import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from starlette import status
from pydantic import BaseModel, Field

from services.database import get_recent_summary, get_summaries_by_dates
from services.date import find_date
from services.whatsapp import send_reply

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

@router.post("/hook", status_code=status.HTTP_200_OK)
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
            reply = getSummaryToResponse(text)
            # You can call the Cloud API here to reply (e.g., using httpx or requests)
            send_reply(phone, f"{reply}")
    except Exception as e:
        print("Error handling message:", e)

    return {"status": "received"}


class TestRequest(BaseModel):
    text: str

@router.post("/testhook", status_code=status.HTTP_200_OK)
async def test_webhook(params: TestRequest):

    text = params.text
    reply = getSummaryToResponse(text)
    # You can call the Cloud API here to reply (e.g., using httpx or requests)
    return {
        reply
    }

def getSummaryToResponse(text):
    dates = find_date(text)
    print(dates)
    if len(dates) > 0:
        reply = "Below is the summary of requested dates\n"
        print("more than 1 day")
        res = get_summaries_by_dates(dates)
        if len(res) == 0:
            reply = "No summary found for the specific dates"
    else:
        reply = "Below is the summary of 5 most recent published news\n"
        print("get 5 recent summary")
        res = get_recent_summary()
    last_keyword = "-1"
    for payload in res:
        keyword = payload["keyword"]
        published_date = payload["published_date"]
        summary = payload["summary"]
        if keyword != last_keyword:
            last_keyword = keyword
            reply = reply + f"\n[{keyword}]\n"
        reply = reply + f"Published date: {published_date}\n" + f"{summary}\n"
    return reply