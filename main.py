from fastapi import FastAPI, Request
import models
from database import engine
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers.task import router as task_router
from routers.auth import router as auth_router
from routers.admin import router as admin_router


app = FastAPI()
app.include_router(task_router)
app.include_router(auth_router)
app.include_router(admin_router)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory='templates/')
app.mount('/static', StaticFiles(directory='static/'), name='static')


@app.get('/')
async def home_function(request: Request):
    return templates.TemplateResponse('home.html', {'request': request})