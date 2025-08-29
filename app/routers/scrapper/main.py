import os
from fastapi import APIRouter, Depends, Request, security, BackgroundTasks
from fastapi.responses import FileResponse
import urllib

from services.database import database
from services.aws_s3 import get_presigned_url
import services.file_write as file_write
from services.jwt import verify_token_from_cookie
import services.scrapper as scrapper
from services.database.keywords.database import get_all_keywords_by_uid
from services.limiter import limiter
from services.llm import article_summary, daily_article_summary
from starlette import status
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio

ENABLE_AI_SUMMARY = os.getenv('ENABLE_AI_SUMMARY')

router = APIRouter(
    prefix='/scrape',
    tags=['scrape'],
    dependencies=[Depends(verify_token_from_cookie)],
)

executor = ThreadPoolExecutor(max_workers=4)

ENABLE_SELENIUM = os.getenv('ENABLE_SELENIUM')

async def scrapping(keyword, regions, max_results):
    try:
        print("starting scrapping for " + keyword)
        region_items = {}
        file_write.create_folder_if_not_exist("./output")

        for region in regions:
            # 1. Scrap links
            name = region["name"]
            k_id = region["k_id"]
            r_id = region["r_id"]
            #news_items = scrapper.get_news_links(keyword, max_results, region["code"], name, k_id, r_id)
            #region_items[name] = news_items

        for region in regions:
            # 2. Selenium
            name = region["name"]
            #maintenance
            if ENABLE_SELENIUM == "1":
                scrapper.scrape_content(name, keyword)
    except Exception as e:
        print("Error occur, but continue the loop")
        print(f"An error occurred: {e}")

def scrapping_once(keyword, regions, max_results, uid):
    try:
        print("starting scrapping for " + keyword)
        region_items = {}
        file_write.create_folder_if_not_exist("./output")

        for region in regions:
            # 1. Scrap links
            name = region["name"]
            k_id = region["k_id"]
            r_id = region["r_id"]
            news_items = scrapper.get_news_links(keyword, max_results, region["code"], name, k_id, r_id)
            region_items[name] = news_items

        for region in regions:
            # 2. Selenium
            name = region["name"]
            #maintenance
            if ENABLE_SELENIUM == "1":
                scrapper.scrape_content(name, keyword)
    except Exception as e:
        print("Error occur, but continue the loop")
        print(f"An error occurred: {e}")



class ScrapeRequest(BaseModel):
    keyword: str
    max_results: int

@router.post("/start", status_code=status.HTTP_200_OK)
async def scrapping_req(params:ScrapeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(scrapping, params.keyword, params.max_results)
    return {
        "message": "success"
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def get_data(token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    return database.fetch_group(uid)


class DownloadRequest(BaseModel):
    region: str

@router.post("/download", status_code=status.HTTP_200_OK)
async def download_data(params:DownloadRequest):
    params.region = urllib.parse.unquote(params.region)
    file_path = f'./output/{params.region}/news_articles.csv'  # Your file path here
    return FileResponse(
        path=file_path,
        filename=params.region,
        media_type="text/csv"
    )

class FetchPageRequest(BaseModel):
    region: str
    published_date: str
    k_id: int

@router.post("/page", status_code=status.HTTP_200_OK)
async def get_page_data(params:FetchPageRequest, token: str = Depends(verify_token_from_cookie)):
    params.region = urllib.parse.unquote(params.region)
    uid = token["uid"]
    return database.fetch_page(params.published_date, params.region, params.k_id, uid)

class FetchPTextRequest(BaseModel):
    id: str

@router.post("/text", status_code=status.HTTP_200_OK)
async def get_page_text(params:FetchPTextRequest):
    text = database.fetch_page_text(params.id)
    return text
    
@router.post("/zip", status_code=status.HTTP_200_OK)
async def get_zip_url(params:FetchPTextRequest):
    zip_path = database.fetch_page_path(params.id)["html_path"]
    url = get_presigned_url(zip_path)
    resp = JSONResponse(content={"url": url}, status_code=status.HTTP_200_OK)
    return resp


class HideQuery(BaseModel):
    region: str
    published_date: str
@router.delete("/remove_news", status_code=status.HTTP_200_OK)
async def remove_news(params: HideQuery = Depends()):
    database.remove_news(params.region, params.published_date)
    return "success"

@router.get("/settings", status_code=status.HTTP_200_OK)
async def get_settings(token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    res = database.get_scrape_setting(uid)
    return res
    
@router.get("/refresh_scrape", status_code=status.HTTP_200_OK)
@limiter.limit("2/minute")
async def refresh_scrape(request: Request, token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    keywords = get_all_keywords_by_uid(uid)
    unique_keywords = set(item["keyword"] for item in keywords)
    loop = asyncio.get_event_loop()
    for keyword in unique_keywords:
        regions = [item for item in keywords if item["keyword"] == keyword]
        loop.run_in_executor(executor, scrapping_once, keyword, regions, 10000, uid)
    return {"message": "success"}
    
@router.get("/refresh_summary", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def refresh_summary(request: Request, token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    if ENABLE_AI_SUMMARY == "1":
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, trigger_daily_summary)
    else: 
        raise Exception("AI_SUMMARY_DISABLED")
    return {"message": "success"}
    
def trigger_daily_summary():
    asyncio.run(daily_summary())
    return "Success"

async def daily_summary():
    task = asyncio.create_task(article_summary())
    await task
    print("Finished Article Summary")
    task = asyncio.create_task(daily_article_summary())
    await task
    print("Finished Daily Summary")
    return "Success"