from fastapi import Request, HTTPException
from sqlalchemy import select
from argon2 import PasswordHasher
import datetime
import jwt
from .db import user, database


def generate_auth_cookie(email: str) -> str:
    auth_token = jwt.encode(
        {
            "email": email,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(days=1),
        },
        "secret",
        algorithm="HS256",
    )
    return auth_token


async def validate_user(request: Request):
    auth_token = request.cookies.get("auth")
    if not auth_token:
        raise HTTPException(
            status_code=303,
            detail="Redirecting to /auth",
            headers={"Location": "/auth"},
        )
    try:
        payload = jwt.decode(auth_token, "secret", algorithms=["HS256"])
        query = select(user).where(
            user.c.email == payload["email"])
        account = await database.fetch_one(query)
        yield account
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=303,
            detail="Redirecting to /auth",
            headers={"Location": "/auth"},
        )


def generate_password(password: str) -> str:
    ph = PasswordHasher()
    return str(ph.hash(password.encode("utf-8")))


def check_password(password: str, encoded_password: str):
    ph = PasswordHasher()
    return ph.verify(encoded_password, password)
