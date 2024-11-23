from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.util import deprecated
from starlette import status
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(
    prefix="/auth",
    tags=['auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


SECRET_KEY = "cb099aafd94ceb88718390eb257b07da23ba64cebe150048f6affdb8b462ac06"
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserRequest(BaseModel):
    username: str
    full_name: str
    password: str
    role: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str



def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, user_role: str, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "user_role": user_role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        user_role: str = payload.get("user_role")
        if not username or not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")
        return {"username": username, "id": user_id, "user_role": user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")


user_dependency = Annotated[dict, Depends(get_current_user)]



@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user_request: UserRequest, db: Session = Depends(get_db)):
    user_model = Users(
        username=user_request.username,
        full_name=user_request.full_name,
        hashed_password=bcrypt_context.hash(user_request.password),
        role=user_request.role,
        is_active=True,
        phone_number=user_request.phone_number
    )

    db.add(user_model)
    db.commit()
    return user_model


@router.post("/token/", response_model=Token)
async def get_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                    db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/get_user")
async def get_user(user: user_dependency, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user['id']).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    return user


@router.put("/change_password/{user_id}")
async def change_password(user_id: int,
                          user_request: UserRequest,
                          db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    user.username = user_request.username
    user.full_name = user_request.full_name
    user.hashed_password = bcrypt_context.hash(user_request.password)
    user.role = user_request.role
    user.phone_number= user_request.phone_number
    db.add(user)
    db.commit()

