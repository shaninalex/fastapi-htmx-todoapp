from datetime import datetime
from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from contextlib import asynccontextmanager
from db import metadata, engine, database, user


metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # query = user.insert().values(
    #     email="test@test.com",
    #     name="test",
    #     password="aadflkjadf",
    #     created_at=datetime.now()
    # )
    # last_record_id = await database.execute(query)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"id": 1}
    )

@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html")

@app.post("/auth")
async def auth_handler(email: Annotated[str, Form()], password: Annotated[str, Form()]):
    print(email)
    print(password)
    return {"email": email, "password": password}

@app.post("/clicked", response_class=HTMLResponse)
async def clicked(request: Request):
    return templates.TemplateResponse(request=request, name="result.html")


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="item.html", context={"id": id}
    )
