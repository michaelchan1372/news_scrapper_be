from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
import services.file_write as file_write
import services.scrapper as scrapper
from starlette import status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix='/scrape',
    tags=['scrape']
)

async def scrapping(keyword, max_results):
    region_items = {}
    file_write.create_folder_if_not_exist("./output")

    regions = scrapper.regions
    for region in regions:
        # 1. Scrap links
        name = region["name"]
        news_items = scrapper.get_news_links(keyword, max_results, region["code"], name)
        region_items[name] = news_items

    for region in regions:
        # 2. Selenium
        name = region["name"]
        news_items = region_items[name]
        scrapper.scrape_content(news_items, name, keyword)

class ScrapeRequest(BaseModel):
    keyword: str
    max_results: int

@router.post("/start", status_code=status.HTTP_200_OK)
async def scrapping_req(params:ScrapeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(scrapping, params.keyword, params.max_results)
    return {
        "message": "success"
    }