from datetime import datetime
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from starlette import status
from pydantic import BaseModel, Field

from services.database import get_recent_summary, get_summaries_by_date_range, get_summaries_by_dates
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
    if len(dates) > 0 and len(dates) != 2:
        reply = "Below is the summary of requested dates\n"
        print("more than 1 day")
        res = get_summaries_by_dates(dates)
        if len(res) == 0:
            reply = "No summary found for the specific dates"
    elif len(dates) == 2:
        sorted_dates = sorted([dates[0], dates[1]], key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
        reply = f"Below is the summary between {sorted_dates[0]} to {sorted_dates[1]}\n"
        res = get_summaries_by_date_range(sorted_dates[0], sorted_dates[1])
        if len(res) == 0:
            reply = "No summary found for the specific date range"
    else:
        reply = "Below is the summaries of news in the recent 5 days:\n"
        print("get 5 recent summary")
        res = get_recent_summary()
    last_keyword = "-1"
    for payload in res:
        keyword = payload["keyword"]
        published_date = payload["published_date"]
        summary = payload["summary"]
        if keyword != last_keyword:
            last_keyword = keyword
            reply = reply + f"\nKeyword: [{keyword}]\n"
        reply = reply + f"\nPublished date: {published_date}\n" + f"{summary}\n"
    return reply