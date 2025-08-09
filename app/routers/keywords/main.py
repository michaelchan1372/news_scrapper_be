from fastapi import APIRouter, Depends, Request
from collections import defaultdict
from services.database.keywords import database
from pydantic import BaseModel
from services.jwt import verify_token_from_cookie
from starlette import status

router = APIRouter(
    prefix='/keywords',
    tags=['keywords'],
    dependencies=[Depends(verify_token_from_cookie)],
)

@router.get("/all", status_code=status.HTTP_200_OK)
def get_all_active_keywords(token: str = Depends(verify_token_from_cookie)):
    keywords = database.get_all_keywords()
    return keywords

@router.get("/keywords", status_code=status.HTTP_200_OK)
def get_all_user_keywords(token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    keywords = database.get_user_keywords(uid)
    grouped = defaultdict(list)
    for keyword in keywords:
        grouped[keyword["keyword"]].append(
            {
                "kur_id": keyword["kur_id"],
                "name": keyword["name"]
            }
            
        )
    result = [
        {
            "keywords": keyword,
            "regions": regions
        }
        for keyword, regions in grouped.items()
    ]
    return result

@router.get("/regions", status_code=status.HTTP_200_OK)
def get_all_regions():
    regions = database.get_available_regions()
    return regions


class Keyword(BaseModel):
    keyword: str


@router.post("/add_keywords")
def add_new_keyword(request: Request, params: Keyword, token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    keyword = params.keyword
    (ku_id, keyword_id) = database.add_keyword(keyword, uid)
    database.add_region_to_keyword(keyword, uid, 2)
    return {
        "ku_id": ku_id,
        "keyword_id": keyword_id
    }
    
class KeywordRegion(BaseModel):
    keyword: str
    region_id: int

@router.post("/add_keyword_region")
def add_new_keyword(request: Request, params: KeywordRegion, token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    keyword = params.keyword
    region_id = params.region_id
    return  {
        "kur_id": database.add_region_to_keyword(keyword, uid, region_id),
    }
    
@router.delete("/remove_keyword_region")
def add_new_keyword(request: Request, params: KeywordRegion = Depends(), token: str = Depends(verify_token_from_cookie)):
    uid = token["uid"]
    keyword = params.keyword
    region_id = params.region_id
    return  {"message": database.remove_region_from_keyword(keyword, uid, region_id)} 
    