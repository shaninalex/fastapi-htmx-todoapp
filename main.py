from datetime import datetime
import time
from typing import Annotated
from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import insert, select
from contextlib import asynccontextmanager

from internal.db import metadata, engine, database, user
from internal.utils import (
    generate_auth_cookie,
    generate_password,
    validate_user,
    check_password,
)


metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Middleware example
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(validate_user)])
async def home(request: Request):
    # Redirecting to auth page
    # return RedirectResponse("/auth")
    return templates.TemplateResponse(request=request, name="home.html")


@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth.html", context={"title": "Login"}
    )


@app.post("/auth")
async def auth_handler(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    try:
        query = select([user.c.password]).where(user.c.email == email)
        account = await database.fetch_one(query)
        check_password(password, account.password)
        response.set_cookie(
            "auth", generate_auth_cookie(email), secure=True, httponly=True
        )
        response.headers["HX-Location"] = "/"
    except Exception as err:
        return templates.TemplateResponse(
            request=request,
            name="components/alert.html",
            context={
                "type": "danger",
                "message": err,
            },
        )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={"title": "Register", "register": True},
    )


@app.post("/register")
async def register_handler(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    try:
        query = insert(user).values(
            email=email,
            name="test",
            password=generate_password(password),
            created_at=datetime.now(),
        )
        await database.execute(query)
        response.set_cookie(
            "auth", generate_auth_cookie(email), secure=True, httponly=True
        )
        response.headers["HX-Location"] = "/"
        return {"status": "ok"}
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
            request=request,
            name="components/alert.html",
            context={
                "type": "danger",
                "message": "Unable to register user",
            },
        )


@app.get("/logout")
def logout(response: Response):
    # Delete the "auth" cookie
    response.delete_cookie(key="auth", path="/", secure=True, httponly=True)
    # Redirect the user to the home page
    response.headers["Location"] = "/"
    response.status_code = 302  # 302 Found (temporary redirect)
    return response


@app.post("/clicked", response_class=HTMLResponse)
async def clicked(request: Request):
    return templates.TemplateResponse(request=request, name="chunks/result.html")


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="item.html", context={"id": id}
    )
