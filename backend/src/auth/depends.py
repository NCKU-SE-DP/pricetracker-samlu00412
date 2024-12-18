from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from jose import jwt,JWTError
from datetime import datetime, timedelta

from src.users.models import User
from src.configs import Constants
from src.database import session_opener
from src.error_handlers.server_exception import InternalServerError

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def verify(password, hashed_password):
    return password_context.verify(password, hashed_password)

# Check whether the hash value of password is same as hashed_password
def check_user_password_is_correct(database, name, password):
    isPasswordCorrect = database.query(User).filter(User.username == name).first()
    if not verify(password, isPasswordCorrect.hashed_password):
        return False
    return isPasswordCorrect

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    database = Depends(session_opener)
):
    payload = jwt.decode(token, Constants.Auth.KEY, algorithms=[Constants.Auth.ENCODING_ALGO])
    return database.query(User).filter(User.username == payload.get("sub")).first()

def create_access_token(data, expires_delta=None):
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=Constants.Auth.DEFAULT_EXPIRED_TIME)
        to_encode.update({"exp": expire})
        print(to_encode)
        encoded_json_webtoken = jwt.encode(to_encode, Constants.Auth.KEY, algorithm=Constants.Auth.ENCODING_ALGO)
        return encoded_json_webtoken
    except JWTError as err:
        raise InternalServerError(err)

