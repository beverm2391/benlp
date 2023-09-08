from fastapi import Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from config import MY_API_KEY

# ! Load Environment Variables -------------------------------------

def check_api_key(api_key: str):
    if api_key is None:
        return JSONResponse(content={"error": "Missing API Key"}, status_code=400)
    elif api_key != MY_API_KEY:
        return JSONResponse(content={"error": "Invalid API key"}, status_code=400)

# https://stackoverflow.com/questions/62882830/fastapi-middleware-on-different-folder-not-working
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-KEY")
        check = check_api_key(api_key)
        if check:
            return check
        response = await call_next(request)
        return response