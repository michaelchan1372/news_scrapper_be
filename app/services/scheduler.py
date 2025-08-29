import asyncio
from contextlib import asynccontextmanager
import os
import threading
import schedule
from fastapi import FastAPI, Depends
import time

from routers.scrapper.main import scrapping
from services.database.keywords.database import get_all_keywords
from services.llm import article_summary, daily_article_summary
from services.database.users.database import get_all_user_notification_settings
from services.database import database
from services.email import send_notification_email

ENABLE_SELENIUM = os.getenv('ENABLE_SELENIUM')
ENABLE_AI_SUMMARY = os.getenv('ENABLE_AI_SUMMARY')
ONLY_SCHEDULE_SCRAPPING = os.getenv('ONLY_SCHEDULE_SCRAPPING')
ONLY_SCHEDULE_AI_SUMMARY = os.getenv('ONLY_SCHEDULE_AI_SUMMARY')
# todo, support db
async def scrapping_action():
    print("Started scheduled job")
    keywords = get_all_keywords()
    unique_keywords = set(item["keyword"] for item in keywords)
    for keyword in unique_keywords:
        regions = [item for item in keywords if item["keyword"] == keyword]
        task = asyncio.create_task(scrapping(keyword, regions, 10000))
        await task
    task = asyncio.create_task(notifiy_user())
    await task
    # to do, udpate db
    print("Finish batch, waiting for next in 4 hours.")
    if ENABLE_SELENIUM == "1" and ENABLE_AI_SUMMARY == "1":
        await daily_summary()
    return "Success"

async def daily_summary():
    task = asyncio.create_task(article_summary())
    await task
    print("Finished Article Summary")
    task = asyncio.create_task(daily_article_summary())
    await task
    print("Finished Daily Summary")
    return "Success"

def run_scheduler():
    if ONLY_SCHEDULE_SCRAPPING == "0":
        asyncio.run(scrapping_action())
    schedule.every(4).hours.do(lambda: asyncio.run(scrapping_action()))
    if ENABLE_AI_SUMMARY == "1":
        print("AI Sumamry is enabled")
        if ONLY_SCHEDULE_AI_SUMMARY == "0":
            print("Running AI Summary at start.")
            asyncio.run(daily_summary())
        schedule.every().day.at("12:00").do(lambda: asyncio.run(daily_summary()))

    while True:
        schedule.run_pending()
        time.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    yield

async def notifiy_user():
    users = get_all_user_notification_settings()
    for user in users:
        last_notified = user["last_notified"]
        uid = user["uid"]
        if user["is_email_notifications"] == 1:
            latest_nis = database.get_user_news_item_latest(last_notified, uid)
            if len(latest_nis) > 0:
                if send_notification_email(user["email"], latest_nis):
                    return
        print(user["email"])