import os
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi import security
from fastapi.responses import FileResponse
import urllib

from services.database import database
from services.aws_s3 import get_presigned_url
import services.file_write as file_write
from services.jwt import verify_token_from_cookie
import services.scrapper as scrapper
from starlette import status
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix='/scrape',
    tags=['scrape'],
    dependencies=[Depends(verify_token_from_cookie)],
)

ENABLE_SELENIUM = os.getenv('ENABLE_SELENIUM')

async def scrapping(keyword, regions, max_results):
    try:
        print("starting scrapping for " + keyword)
        print(regions)
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

@router.post("/page", status_code=status.HTTP_200_OK)
async def get_page_data(params:FetchPageRequest):
    params.region = urllib.parse.unquote(params.region)
    return database.fetch_page(params.published_date, params.region)

class FetchPTextRequest(BaseModel):
    id: str

@router.post("/text", status_code=status.HTTP_200_OK)
async def get_page_text(params:FetchPTextRequest):
    text = database.fetch_page_text(params.id)
    return text
    
@router.post("/zip", status_code=status.HTTP_200_OK)
async def get_zip_url(params:FetchPTextRequest):
    print("KDSFJSDALFKJDSFLK")
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