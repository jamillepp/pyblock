"""Main application entry point for the FastAPI application."""

from fastapi import FastAPI
from app.api import wallets, transactions
from app.db.session import engine
from app.db import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(wallets.router, prefix="/wallets")
app.include_router(transactions.router, prefix="/transactions")
