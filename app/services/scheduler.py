import asyncio
from contextlib import asynccontextmanager
import threading
import schedule
from fastapi import FastAPI, Depends
import time

from routers.scrapper.main import scrapping

# todo, support db
keywords = ["郭鳳儀", "Anna Kwok", "郭賢生", "Yin Sang Kwok", "HKDC", "香港民主委員會"]

async def scrapping_action():
    print("Started scheduled job")
    for keyword in keywords:
        task = asyncio.create_task(scrapping(keyword, 10000))
        await task
    # to do, udpate db
    print("Finish batch, waiting for next in 4 hours.")
    return "Success"

def run_scheduler():
    asyncio.run(scrapping_action())
    schedule.every(4).hours.do(lambda: asyncio.run(scrapping_action()))

    while True:
        schedule.run_pending()
        time.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    yield


    