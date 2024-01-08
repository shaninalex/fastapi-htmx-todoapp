from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import metadata, engine, database, user


metadata.create_all(engine)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    query = user.insert().values(
        email="test@test.com",
        name="test",
        password="aadflkjadf",
        created_at=datetime.now()
    )
    last_record_id = await database.execute(query)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"id": last_record_id}
    )


@app.post("/clicked", response_class=HTMLResponse)
async def clicked(request: Request):
    return templates.TemplateResponse(request=request, name="result.html")


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="item.html", context={"id": id}
    )
