"""Wallet API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import models, schemas
from app.core import eth, utils
from app.db.session import get_db
from app.core.logger import logger

router = APIRouter()

@router.post("/", response_model=schemas.WalletCreateResponse)
def create_wallets(qtd: int, db: Session = Depends(get_db)):
    """Create multiple wallets and save them to the database."""
    logger.info(f"Request to create {qtd} wallets received")

    if qtd <= 0 or qtd > 50:
        logger.error("Invalid quantity {qtd} for wallet creation. Must be between 1 and 50.")
        raise HTTPException(status_code=400, detail="Quantidade inválida")

    wallets = []
    for _ in range(qtd):
        address, private_key = eth.create_wallet()
        encrypted_key = utils.encrypt_private_key(private_key)

        wallet = models.Wallet(
            address=address,
            private_key=encrypted_key,
        )
        db.add(wallet)
        wallets.append(address)

    logger.info(f"{qtd} wallets created successfully. Saving to database.")

    db.commit()

    logger.info("Wallets saved to database successfully.")

    return {"message": f"{qtd} carteiras criadas com sucesso", "addresses": wallets}

@router.get("/", response_model=list[schemas.WalletOut])
def list_wallets(db: Session = Depends(get_db)):
    """List all wallets stored in the database."""
    logger.info("Request to list all wallets received")

    wallets = db.query(models.Wallet).all()

    logger.info(f"Retrieved {len(wallets)} wallets from the database")

    return wallets
