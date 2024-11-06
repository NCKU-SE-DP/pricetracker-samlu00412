from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import session_opener
from ..auth.depends import (check_user_password_is_correct,create_access_token,
                            authenticate_user_token,password_context)
from .models import User
from .schemas import UserAuthSchema

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
    user = check_user_password_is_correct(database, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def create_new_user(user: UserAuthSchema, database: Session = Depends(session_opener)):
    hashed_password = password_context.hash(user.password)
    database_user = User(username=user.username, hashed_password=hashed_password)
    database.add(database_user)
    database.commit()
    database.refresh(database_user)
    return database_user

@router.get("/me")
def read_users_name(user=Depends(authenticate_user_token)):
    return {"username": user.username}
