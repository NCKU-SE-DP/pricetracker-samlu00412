from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
from sentry_sdk import capture_exception
from src.database import session_opener
from src.auth.depends import (check_user_password_is_correct,create_access_token,
                            authenticate_user_token,password_context)
from src.configs import Constants
from src.users.models import User
from src.users.schemas import UserAuthSchema
from src.error_handlers.user_exceptions import UserAlreadyExistError,InvalidError
from src.error_handlers.server_exception import InternalServerError

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404:{"Description" : "Not found"}}
)

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(session_opener)
):
    """Login and verify user"""
    logging.debug(f"Login initialised: {form_data.username}")
    user = check_user_password_is_correct(database, form_data.username, form_data.password)
    if not user:
        logging.debug(f"Failed to login: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    try:
        access_token = create_access_token(
            data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
        )
    except Exception as e:
        capture_exception(e)
        return HTTPException(status_code=400, detail="Something went wrong while processing the request")
    logging.debug(f"Logged in: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def create_new_user(user: UserAuthSchema, database: Session = Depends(session_opener)):
    logging.debug(f"Creating user: {user.username}")
    hashed_password = password_context.hash(user.password)
    database_user = User(username=user.username, hashed_password=hashed_password)
    database.add(database_user)
    database.refresh(database_user)
    logging.debug(f"Created user: {user.username}")
    return database_user

@router.get("/me")
def read_users_name(user=Depends(authenticate_user_token)):
    logging.debug(f"Accessed /api/v1/users/me: {user.username}")
    return {"username": user.username}
