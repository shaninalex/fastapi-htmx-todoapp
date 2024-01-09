from typing import Annotated

from fastapi import Header, Request


def generate_auth_cookie(email: str) -> str:
    return f"auth cookie for {email}"


def validate_user(request: Request):
    print(request)
