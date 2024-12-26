from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from jose import jwt,JWTError
from jose.exceptions import ExpiredSignatureError
from datetime import datetime, timedelta
import logging
from sentry_sdk import capture_exception
from src.users.models import User
from src.configs import Constants
from src.database import session_opener
from src.error_handlers.server_exception import InternalServerError
from src.auth.exceptions import handle_exception

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def verify(password, hashed_password):
    return password_context.verify(password, hashed_password)

# Check whether the hash value of password is same as hashed_password
def check_user_password_is_correct(database, name, password):
    userdata = database.query(User).filter(User.username == name).first()
    try:
        if not verify(password, userdata.hashed_password):
            return False
    except Exception as e:
        logging.error(f"Failed to verify password: {e}")
        capture_exception(e)
        return False
    return userdata

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    database = Depends(session_opener)
):
    try:
        logging.debug(f"Authenticating token: {token[:10]}...")
        payload = jwt.decode(token, Constants.Auth.KEY, algorithms=["HS256"])
    except ExpiredSignatureError as e:
        handle_exception(e,"Token expired")
    except JWTError as e:
        handle_exception(e,"Token invalid")
    except Exception as e:
        handle_exception(e,"Failed to authenticate token")
        
    return database.query(User).filter(User.username == payload.get("sub")).first()

def create_access_token(data, expires_delta=None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Constants.Auth.DEFAULT_EXPIRED_TIME)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, Constants.Auth.KEY, algorithm=Constants.Auth.ENCODING_ALGO)
    except Exception as e:
        logging.error(f"Error while encoding with jwt: {e}")
        raise e
    return encoded_jwt

