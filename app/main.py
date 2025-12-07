from fastapi import FastAPI
from dotenv import load_dotenv

# 引入webhook 
from app.routers.webhook import router as webhook_router
from app.routers.landinfo import router as landinfo_router

load_dotenv()

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
