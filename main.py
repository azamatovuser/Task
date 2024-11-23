from fastapi import FastAPI
import models
from database import engine
from routers.task import router as task_router
from routers.auth import router as auth_router
from routers.admin import router as admin_router

app = FastAPI()
app.include_router(task_router)
app.include_router(auth_router)
app.include_router(admin_router)

models.Base.metadata.create_all(bind=engine)