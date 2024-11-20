from router import path1, path2, path3
from fastapi import FastAPI
import os
os.environ['OPENAI_API_KEY'] = "sk-xxx"

app = FastAPI()
app.include_router(path1.router)
app.include_router(path2.router)
app.include_router(path3.router)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}
