from datetime import datetime, timedelta
import os
import re
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Query, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from services.database.users import database
from services.email import send_verification_email
from services.limiter import limiter
from services.jwt import REFRESH_TOKEN_NAME, TOKEN_COOKIE_NAME, create_access_token, get_password_hash, verify_password, verify_refresh_token_from_cookie
from pydantic import BaseModel
from starlette import status

IS_PRODUCTION=os.getenv("IS_PRODUCTION")

domain = None
samesite="lax"

if IS_PRODUCTION == "1":
    domain = ".safersearch.org"
    samesite="none"

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = database.get_user_data(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if user["is_active"] == 0:
        raise HTTPException(status_code=400, detail="user not active")
    access_token = create_access_token(data={"sub": user["username"], "uid": user["id"]}, expires_delta=timedelta(minutes=60))
    refresh_token = create_access_token(data={"sub": user["username"], "uid": user["id"]}, expires_delta=timedelta(days=7))
    resp = JSONResponse(content={"message": "Login successful"}, status_code=status.HTTP_200_OK)
    resp.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=IS_PRODUCTION == "1",  # only over HTTPS
        samesite=samesite,  # or "strict"
        domain=domain,
        max_age=60 * 60,
        path="/"
    )
    resp.set_cookie(
        key=REFRESH_TOKEN_NAME,
        value=refresh_token,
        httponly=True,
        secure=IS_PRODUCTION == "1",
        samesite=samesite,
        domain=domain,
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/auth/refresh"
    )
    return resp


class User(BaseModel):
    username: str
    password: str
    email: str


@router.post("/create", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def create_user(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    domain: Annotated[str, Form()]
):
    params = User(email=email, username=username, password=password)
    is_data_valid = validate_data(params)
    if not is_data_valid:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    hash = get_password_hash(params.password)
    [success, user_id] = database.create_users(params, hash)
    
    if success:
        code = send_verification_email(params.email)
        database.update_verification_code(user_id, code)
        
        return {"message": "Create user successful"}
    else:
        raise HTTPException(status_code=400, detail="user exists")
    

def validate_data(user: User):
    is_email_valid = is_valid_email(user.email)
    return is_email_valid

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

class UserEmail(BaseModel):
    email: str

@router.post("/resend", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def resend_verifciation_code(request: Request, params:UserEmail):
    user = database.get_user_data(params.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    code = send_verification_email(params.email)
    database.update_verification_code(user["id"], code)
    return {"message": "success"}

class UserEmailVericiation(BaseModel):
    email: str
    code: str
@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_email(params: UserEmailVericiation, response: Response):
    user = database.get_user_data(params.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if user["is_active"] == 1:
        raise HTTPException(status_code=400, detail="ALREADY_ACTIVATED")
    if datetime.fromisoformat(str(user["verification_expired"])) < datetime.now():
        raise HTTPException(status_code=400, detail="Verification Expired")
    if user["verification_failed"] and user["verification_failed"] > 5:
        raise HTTPException(status_code=400, detail="Failed too many times, please contect admin.")
    if user["verification_code"] == params.code:
        database.update_user_verification_success(user["id"])
    else:
        if user["verification_failed"] == 0 or user["verification_failed"]:
            database.update_user_verification_failed(user["verification_failed"] + 1, user["id"])
        raise HTTPException(status_code=400, detail="Verification Code Not Match")
    access_token = create_access_token(data={"sub": user["username"], "uid": user["id"]}, expires_delta=timedelta(minutes=60))
    refresh_token = create_access_token(data={"sub": user["username"], "uid": user["id"]}, expires_delta=timedelta(days=7))
    response.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=IS_PRODUCTION == "1",  # only over HTTPS
        samesite=samesite,  # or "strict"
        domain=domain,
        max_age=60 * 60,
        path="/"
    )
    response.set_cookie(
        key=REFRESH_TOKEN_NAME,
        value=refresh_token,
        httponly=True,
        secure=IS_PRODUCTION == "1",
        samesite=samesite,
        domain=domain,
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/auth/refresh"
    )
    return {"message": "success"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=TOKEN_COOKIE_NAME,
        domain=domain,
        secure=IS_PRODUCTION == "1", 
        httponly=True,
        samesite=samesite,
        path="/",           # Must match the original cookie's path!
    )
    response.delete_cookie(
        key=REFRESH_TOKEN_NAME,
        domain=domain,
        secure=IS_PRODUCTION == "1", 
        httponly=True,
        samesite=samesite,
        path="/auth/refresh",           # Must match the original cookie's path!
    )
    return {"message": "Logged out"}

@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_token(token: str = Depends(verify_refresh_token_from_cookie)):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        print(token)
        uid = token["uid"]
        username = token["sub"]
        if username is None or uid is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        new_access_token = create_access_token(data={"sub": username, "uid": uid}, expires_delta=timedelta(minutes=60))
        response = JSONResponse(content={"message": "Token refreshed"})
        response.set_cookie(
            key=TOKEN_COOKIE_NAME,
            value=new_access_token,
            httponly=True,
            secure=IS_PRODUCTION == "1",
            samesite=samesite,
            domain=domain,
            max_age=60 * 60,  # 1 hour
            path="/"
        )
        return response
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid refresh token")