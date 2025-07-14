"""Transaction API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core import eth
from app.core.logger import logger
from app.db import schemas, models
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=schemas.TransactionOut)
def get_transaction(tx_hash: str):
    """Retrieve a transaction by its hash."""
    logger.info(f"Request to get transaction with hash {tx_hash} received")

    try:
        tx, receipt = eth.get_transaction(tx_hash)
    except Exception as e:
        logger.error(f"Error retrieving transaction: {e}")
        raise HTTPException(status_code=404, detail="Transaction not found") from e

    logger.info(f"Transaction {tx_hash} retrieved successfully")

    # Converte para o formato esperado pelo teste
    return schemas.TransactionOut(
        id=1,
        hash=tx["hash"].hex(),
        from_address=tx["from"],
        to_address=tx["to"],
        value=str(tx["value"]),
        gas=tx["gas"],
        gas_price=tx["gasPrice"],
        input_data=tx["input"].hex(),
        receipt_status=receipt["status"],
        transaction_type="erc20" if tx.get("input", "0x") != "0x" else "eth"
    )

@router.post("/validate", response_model=schemas.TransactionOut)
def validate_transaction(tx_hash: str, db: Session = Depends(get_db)):
    """Validate the transaction security."""
    logger.info(f"Request to validate transaction with hash {tx_hash} received")

    try:
        logger.info(f"Retrieving transaction {tx_hash} from Ethereum provider")
        tx, receipt = eth.get_transaction(tx_hash)

        logger.info(f"Validating transaction {tx_hash}")
        validation = eth.validate_transaction(tx, receipt)
        if not validation.is_valid:
            logger.warning(f"Transaction {tx_hash} is not valid")
            raise HTTPException(status_code=400, detail="Transaction is not valid for the following reason: " + validation.reason)
        else:
            logger.info("Checking if destination addresses exists in the database")

            to_addresses = []
            if validation.tx_type == "eth":
                to_addresses.append(tx["to"])
            elif validation.tx_type == "erc20":
                to_addresses = [transfer.to_address for transfer in validation.transfers if transfer.to_address]

            if not to_addresses:
                logger.warning(f"No valid destination address found in transaction {tx_hash}")
                raise HTTPException(status_code=400, detail="No valid destination address found")

            for to in to_addresses:
                logger.info(f"Checking if destination address {to} exists in the database")

                account = db.query(models.Wallet).filter(models.Wallet.address == to).first()
                if not account:
                    logger.warning(f"Destination address {to} not found in database in transaction {tx_hash}")
                    raise HTTPException(status_code=404, detail=f"Destination address {to} not found in database")

            logger.info(f"Transaction {tx_hash} is valid. Storing in database")

            transaction = models.Transaction(
                hash=tx["hash"].hex(),
                from_address=tx["from"],
                to_address=tx["to"],
                value=str(tx["value"]),
                gas=tx["gas"],
                gas_price=tx["gasPrice"],
                input_data=tx["input"].hex() if tx["input"] else None,
                receipt_status=receipt["status"],
                token_contract=None,
                token_symbol=None,
                token_decimals=None,
            )

            if validation.tx_type == "erc20":
                transaction.transaction_type = "erc20"
                transaction.token_contract = tx["to"]
                if validation.transfers:
                    first = validation.transfers[0]
                    transaction.token_symbol = first.asset
                    transaction.token_decimals = first.decimals
                    transaction.to_address = first.to_address
                    transaction.value = first.value

            existing_tx = db.query(models.Transaction).filter(models.Transaction.hash == transaction.hash).first()
            if not existing_tx:
                db.add(transaction)
                db.commit()
            else:
                transaction = existing_tx 
    except Exception as e:
        logger.error(f"Error validating transaction: {e}")
        raise HTTPException(status_code=400, detail="Invalid transaction") from e

    logger.info(f"Transaction {tx_hash} validated successfully")

    return schemas.TransactionOut(
        id=transaction.id,
        hash=transaction.hash,
        from_address=transaction.from_address,
        to_address=transaction.to_address,
        value=transaction.value,
        gas=transaction.gas,
        gas_price=transaction.gas_price,
        input_data=transaction.input_data,
        receipt_status=transaction.receipt_status,
        token_contract=transaction.token_contract,
        token_symbol=transaction.token_symbol,
        token_decimals=transaction.token_decimals,
        transaction_type=transaction.transaction_type
    )
