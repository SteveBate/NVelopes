from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from .models import TokenData, User, UserInDB
from .db import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# openssl rand -hex 32
SECRET_KEY = "0c8eaab3eba38db00e17358b08dd28425b14561f2ec174a4b75ee3c566e92e15"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db, username: str, password: str):
    print("authenticate_user")
    user = __get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def __get_current_user(token: str = Depends(oauth2_scheme)):
    print("get_current_user")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise credentials_exception
        token_data = TokenData(username=username)
        user = __get_user(db, username=token_data.username)
        if user is None: raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


def __get_user(db, username: str):
    print("get_user: " + username)
    match = db.get_user(username)    
    user = UserInDB(**match) if match else None
    if user:
        user.user_id = str(match["_id"])
    return user


async def get_current_active_user(current_user: User = Depends(__get_current_user)):
    print("get_current_active_user")
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

