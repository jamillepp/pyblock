from fastapi import FastAPI
from app.api import wallets
from app.db.session import engine
from app.db import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the PyBlock API!"}

app.include_router(wallets.router, prefix="/wallets")
