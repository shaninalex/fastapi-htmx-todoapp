from fastapi import Request, Response
import datetime
import jwt

def generate_auth_cookie(email: str) -> str:
    auth_token = jwt.encode({
        "email": email,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=30),
    }, "secret", algorithm="HS256")
    return auth_token


def validate_user(request: Request, response: Response):
    auth_token = request.cookies.get('auth')
    if not auth_token:
        print("not authenticated. Redirect to auth page")
    print(auth_token)
