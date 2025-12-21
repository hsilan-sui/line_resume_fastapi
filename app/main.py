from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os



# 引入webhook 
from app.routers.webhook import router as webhook_router
from app.routers.landinfo import router as landinfo_router

# load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent  # app/ 的上一層 = 專案根
load_dotenv(BASE_DIR / ".env")
print("NODE_LANDINFO_URL =", os.getenv("NODE_LANDINFO_URL"))

app = FastAPI()

app.include_router(webhook_router)

# 新增landinfoRouter
app.include_router(landinfo_router)

# ============
# API endpoint
# ============
@app.get("/")
async def root():
    return {"message": "FastAPI LINE Bot is running"}
