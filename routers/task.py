from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from routers.auth import get_current_user
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Task

router = APIRouter(
    prefix='/task',
    tags=['task']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/")
async def read_tasks(user: user_dependency, db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')
    return db.query(Task).filter(Task.owner_id == user.get('id')).all()


@router.get("/{task_id}/")
async def read_task(user: user_dependency, task_id: int, db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')
    task_model = db.query(Task).filter(task_id == Task.id).filter(Task.owner_id == user.get('id')).first()
    if task_model:
        return task_model
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/create_task/")
async def create_task(user: user_dependency, task_request: TaskRequest, db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')
    task_model = Task(**task_request.model_dump(), owner_id=user.get('id'))

    db.add(task_model)
    db.commit()


@router.put("/update_task/{task_id}/")
async def update_task(user: user_dependency, task_request: TaskRequest, task_id: int, db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')
    task_model = db.query(Task).filter(task_id == Task.id).filter(Task.owner_id == user.get('id')).first()
    if task_model:
        task_model.title = task_request.title
        task_model.description = task_request.description
        task_model.priority = task_request.priority
        task_model.complete = task_request.complete

        db.add(task_model)
        db.commit()
        return HTTPException(status_code=200, detail="Changed")
    raise HTTPException(status_code=404, detail="Task not found")


@router.delete("/delete_task/{task_id}/")
async def delete_task(user: user_dependency, task_id: int, db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')
    task_model = db.query(Task).filter(task_id == Task.id).filter(Task.owner_id == user.get('id')).first()
    if task_model:
        db.query(Task).filter(task_id == Task.id).filter(Task.owner_id == user.get('id')).delete()
        db.commit()
        return HTTPException(status_code=200, detail="Deleted")
    raise HTTPException(status_code=404, detail="Task not found")
