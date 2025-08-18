from fastapi import APIRouter, Depends


from services.database.navigation import database

from services.jwt import verify_token_from_cookie
from starlette import status

router = APIRouter(
    prefix='/navigation',
    tags=['navigation'],
    dependencies=[Depends(verify_token_from_cookie)],
)

@router.get("/all", status_code=status.HTTP_200_OK)
def get_all_active_path():
    paths = database.get_all_path()
    active_paths = [item for item in paths if item["is_active"] == 1]
    return active_paths

@router.get("/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard():
    paths = database.get_all_path()
    active_paths = [item for item in paths if item["is_dashboard"] == 1]
    return active_paths
