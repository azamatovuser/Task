from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from routers.auth import get_current_user
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Task

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/all_tasks")
async def get_all_tasks(user: user_dependency, db: Session = Depends(get_db)):
    if not user or user.get("user_role") != "admin":
        return HTTPException(status_code=401, detail='Authentication failed')
    return db.query(Task).all()


@router.delete("/delete/{task_id}")
async def delete_task(user: user_dependency, task_id: int, db: Session = Depends(get_db)):
    if not user or user.get("user_role") != "admin":
        return HTTPException(status_code=401, detail='Authentication failed')
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return HTTPException(status_code=404, detail='Task not found')
    db.query(Task).filter(Task.id == task_id).delete()
    db.commit()
    return {"message": "Successfully deleted"}