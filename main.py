from datetime import datetime
import time
from typing import Annotated, Any
from fastapi import Depends, FastAPI, Request, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import insert, select, delete, update
from contextlib import asynccontextmanager

from internal.db import metadata, database, engine, user, task, checkbox
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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request,
               account: Annotated[Any, Depends(validate_user)]):
    tasks_query = select(task).where(task.c.user_id == account.id)
    tasks = await database.fetch_all(tasks_query)
    tasks_list = []
    for t in tasks:
        checkboxes = await database.fetch_all(select(checkbox).where(
            checkbox.c.task_id == t.id
        ))
        tasks_list.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "completed": t.completed,
            "checkboxes": checkboxes
        })

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "tasks": tasks_list,
            "account": account
        })


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
        account: Any = await database.fetch_one(query)
        if not account:
            raise Exception("Invalid credentials")
        check_password(password, account.password)
        response.set_cookie(
            "auth", generate_auth_cookie(email), secure=True, httponly=True
        )
        response.status_code = 303
        response.headers["Location"] = "/"
        return response
    except Exception as err:
        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={
                "title": "Login",
                "error": err,
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
        response.status_code = 303
        response.headers["Location"] = "/"
        return response
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


@app.post("/task")
async def create_task(request: Request,
                      taskname: Annotated[str, Form()],
                      account: Annotated[Any, Depends(validate_user)]):
    try:
        query = insert(task).values(
            name=taskname,
            user_id=account.id
        )
        inserted_row_id = await database.execute(query)
        return templates.TemplateResponse(
            request=request,
            name="chunks/task-card.html",
            status_code=201,
            context={
                "task": {
                    "id": inserted_row_id,
                    "name": taskname,
                }
            },
        )
    except Exception as err:
        return templates.TemplateResponse(
            request=request,
            name="components/alert.html",
            status_code=400,
            context={
                "type": "danger",
                "message": err,
            },
        )


@app.delete("/task/{id}")
async def delete_task(id: str,
                      account: Annotated[Any, Depends(validate_user)]):
    await database.execute(delete(task).where(
        task.c.id == id,
        task.c.user_id == account.id
    ))
    return None


# get task form html
@app.get("/task/{id}/edit")
async def get_task_form(id: str,
                        request: Request,
                        account: Annotated[Any, Depends(validate_user)]):
    query = select(task).where(task.c.id == id, task.c.user_id == account.id)
    task_item = await database.fetch_one(query)
    return templates.TemplateResponse(
        request=request,
        name="chunks/task-form.html",
        status_code=200,
        context={
            "task": task_item
        },
    )


@app.patch("/task/{task_id}/checkbox/{checkbox_id}")
async def patch_checkbox(
    task_id: str,
    checkbox_id: str,
    request: Request,
        account: Annotated[Any, Depends(validate_user)]):

    check = await database.fetch_one(select(checkbox).where(
        checkbox.c.task_id == task_id,
        checkbox.c.id == checkbox_id,
    ))

    comp = not check.completed

    await database.fetch_one(
        update(checkbox).values({
            "completed": comp,
        }).where(
            checkbox.c.task_id == task_id,
            checkbox.c.id == checkbox_id,
        ))

    return templates.TemplateResponse(
        request=request,
        name="chunks/checkbox-item.html",
        status_code=200,
        context={
            "task": {
                "id": task_id,
            },
            "c": {
                "id": check.id,
                "name": check.name,
                "completed": comp,
            }
        }
    )


@ app.patch("/task/{id}")
async def patch_task(id: str,
                     name: Annotated[str, Form()],
                     description: Annotated[str, Form()],
                     request: Request,
                     account: Annotated[Any, Depends(validate_user)]):
    await database.fetch_one(
        update(task).values({
            "name": name,
            "description": description
        }).where(task.c.id == id)
    )
    query = select(task).where(task.c.id == id, task.c.user_id == account.id)
    t = await database.fetch_one(query)
    checkboxes = await database.fetch_all(select(checkbox).where(
        checkbox.c.task_id == t.id
    ))
    return templates.TemplateResponse(
        request=request,
        name="chunks/task-card.html",
        status_code=200,
        context={"task": {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "completed": t.completed,
            "checkboxes": checkboxes
        }},
    )


@app.get("/logout")
def logout(response: Response):
    response.delete_cookie(key="auth", path="/", secure=True, httponly=True)
    response.headers["Location"] = "/"
    response.status_code = 302
    return response

# @app.post("/clicked", response_class=HTMLResponse)
# async def clicked(request: Request):
#     return templates.TemplateResponse(request=request, name="chunks/result.html")
#
#
# @app.get("/items/{id}", response_class=HTMLResponse)
# async def read_item(request: Request, id: str):
#     return templates.TemplateResponse(
#         request=request, name="item.html", context={"id": id}
#     )
