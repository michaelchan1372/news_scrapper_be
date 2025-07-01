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

ENABLE_SELENIUM = os.getenv('ENABLE_SELENIUM')
ENABLE_AI_SUMMARY = os.getenv('ENABLE_AI_SUMMARY')

# todo, support db


async def scrapping_action():
    print("Started scheduled job")
    keywords = get_all_keywords()
    unique_keywords = set(item["keyword"] for item in keywords)
    for keyword in unique_keywords:
        regions = [item for item in keywords if item["keyword"] == keyword]
        task = asyncio.create_task(scrapping(keyword, regions, 10000))
        await task
    # to do, udpate db
    print("Finish batch, waiting for next in 4 hours.")
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
    if ENABLE_SELENIUM == "1":
        print("SELENIUM is enabled")
        asyncio.run(scrapping_action())
        schedule.every(4).hours.do(lambda: asyncio.run(scrapping_action()))
    if ENABLE_AI_SUMMARY == "1":
        print("AI Sumamry is enabled")
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


    