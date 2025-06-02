from typing import Annotated
from fastapi import FastAPI, Depends
import routers as router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.scheduler import lifespan

app = FastAPI(lifespan=lifespan)

load_dotenv()

origins = [
    "https://news-scrapper-ct8mo42gy-michael-chans-projects-4c4a7c7d.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.scrapper_router)
app.include_router(router.whatsapp_hook_router)