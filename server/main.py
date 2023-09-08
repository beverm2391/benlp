from fastapi import FastAPI

from typing import List
import time
from fastapi.middleware.cors import CORSMiddleware
from middleware import APIKeyMiddleware
from fastapi import Depends

# ! Import Routers -------------------------------------
from chat import router as chat_router
from chain import router as chain_router
from files import router as files_router

# ! START CONFIG ------------------------------------
app = FastAPI()

# ! Middleware -------------------------------------

# this middleware has to be added before the CORS middleware as to not block the CORS preflight request
# app.add_middleware(APIKeyMiddleware)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("CORS middleware added")

# https://stackoverflow.com/questions/59965872/how-to-solve-no-attribute-routes-in-fastapi
app.include_router(chat_router.router, prefix="/chat", tags=["chat"])
app.include_router(chain_router.router, prefix="/chain", tags=["chain"])
app.include_router(files_router.router, prefix="/files", tags=["files"])

# ! START ROUTES -------------------------------------

@app.get("/")
async def get_index():
    return {"message": "Hello World!"}

@app.get("/test")
async def get_test():
    return {"message": "Test successful!"}