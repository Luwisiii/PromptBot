from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Prompt Bot Microservice")

app.include_router(router)