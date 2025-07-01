import os
from typing import Annotated
from fastapi import FastAPI, Depends
import routers as router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.limiter import limiter
from services.scheduler import lifespan
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(lifespan=lifespan)

load_dotenv()


IS_PRODUCTION=os.getenv("IS_PRODUCTION")

allow_origins = ["*"]

if IS_PRODUCTION == "1":
    allow_origins = ["https://www.safersearch.org"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)  # Optional: middleware support

app.include_router(router.scrapper_router)
app.include_router(router.whatsapp_hook_router)
app.include_router(router.auth_router)
app.include_router(router.nav_router)
app.include_router(router.keyword_router)


