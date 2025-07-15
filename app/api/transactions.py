"""Transaction API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, selectinload
from app.core import eth, utils
from app.core.logger import logger
from app.db import schemas, models
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.CreateTransactionResponse)
def create_transaction(transaction: schemas.TransactionIn, db: Session = Depends(get_db)):
    """Create a new transaction."""
    logger.info(f"Request to create transaction from {transaction.from_address} to {transaction.to_address} received")

    try:
        if not transaction.from_address or not transaction.to_address:
            raise HTTPException(status_code=400, detail="From and To addresses are required")
        if transaction.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")

        account = db.query(models.Wallet).filter(models.Wallet.address == transaction.from_address).first()
        if not account:
            raise HTTPException(status_code=404, detail="From address not found in database")

        decrypted_private_key = utils.decrypt_private_key(account.private_key)
        if not decrypted_private_key:
            raise HTTPException(status_code=403, detail="Invalid private key for the provided address")

        transaction_out = eth.create_transaction(transaction, decrypted_private_key)
        logger.info(f"Transaction created successfully with hash {transaction_out.hash}")

        db_transaction = models.Transaction(
            hash=transaction_out.hash,
            from_address=transaction_out.from_address,
            to_address=transaction_out.to_address,
            value=transaction_out.value,
            gas=transaction_out.gas,
            gas_price=transaction_out.gas_price,
            input_data=transaction_out.input_data,
            receipt_status=transaction_out.receipt_status,
            token_contract=transaction_out.token_contract,
            token_symbol=transaction_out.token_symbol,
            token_decimals= transaction_out.token_decimals,
            transaction_type=transaction_out.transaction_type
        )

        db_transfer = models.Transfer(
            transaction_id=db_transaction.id,
            asset=transaction.asset,
            from_address=transaction.from_address,
            to_address=transaction.to_address,
            value=transaction.amount,
            decimals=transaction_out.token_decimals if transaction_out.token_decimals else 18
        )
        db_transaction.transfers.append(db_transfer)
        
        db.add(db_transaction)
        db.commit()

        return schemas.CreateTransactionResponse(
            message="Transaction created successfully",
            transaction_hash=transaction_out.hash
        )
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to create transaction") from e


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

@router.get("/validate", response_model=schemas.ValidateTransactionResponse)
def validate_transaction(tx_hash: str, db: Session = Depends(get_db)):
    """Validate the transaction security."""
    logger.info(f"Request to validate transaction with hash {tx_hash} received")

    validation =None

    try:
        logger.info(f"Retrieving transaction {tx_hash} from Ethereum provider")
        try:
            tx, receipt = eth.get_transaction(tx_hash)
        except Exception as e:
            logger.error(f"Error retrieving transaction {tx_hash}: {e}")
            if f"Transaction with hash: '{tx_hash}' not found." in str(e):
                logger.error(f"Transaction {tx_hash} not found: {e}")
                return schemas.ValidateTransactionResponse(
                    tx_type=None,
                    hash=tx_hash,
                    is_valid=False,
                    reason="Transaction not found",
                    transfers=[]
                )
            else:
                logger.error(f"Error retrieving transaction {tx_hash}: {e}")
                raise HTTPException(status_code=400, detail="Invalid transaction") from e

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
                    return schemas.ValidateTransactionResponse(
                        tx_type=validation.tx_type,
                        hash=tx_hash,
                        is_valid=False,
                        reason=f"Destination address {to} not found in database",
                    )

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

            for transfer in validation.transfers:
                db_transfer = models.Transfer(
                    asset=transfer.asset,
                    transaction_id=transaction.id,
                    from_address=transfer.from_address,
                    to_address=transfer.to_address,
                    value=transfer.value,
                    decimals=transfer.decimals
                )
                transaction.transfers.append(db_transfer)

            if validation.tx_type == "erc20":
                transaction.transaction_type = "erc20"
                transaction.token_contract = tx["to"]
                if validation.transfers:
                    first = validation.transfers[0]
                    transaction.token_symbol = first.asset
                    transaction.token_decimals = first.decimals
                    transaction.to_address = first.to_address
                    transaction.value = first.value

            existing_tx = db.query(models.Transaction).filter(
                    models.Transaction.hash == transaction.hash
                ).first()
            if not existing_tx:
                db.add(transaction)
                db.commit()
            else:
                transaction = existing_tx 
    except Exception as e:
        logger.error(f"Error validating transaction: {e}")
        raise HTTPException(status_code=400, detail="Invalid transaction") from e

    if not validation:
        logger.error(f"Transaction {tx_hash} validation failed")
        raise HTTPException(status_code=400, detail="Transaction validation failed")

    logger.info(f"Transaction {tx_hash} validated successfully")

    return validation

@router.get("/account", response_model=schemas.AccountTransactionsResponse)
def get_account_transactions(address: str, db: Session = Depends(get_db)):
    """Retrieve all transactions for a given account address."""
    logger.info(f"Request to get transactions for account {address} received")

    try:
        transactions = db.query(models.Transaction).options(
            selectinload(models.Transaction.transfers)
        ).filter(
            (models.Transaction.from_address == address) |
            (models.Transaction.to_address == address)
        ).all()

        if not transactions:
            logger.warning(f"No transactions found for account {address}")
            raise HTTPException(status_code=404, detail="No transactions found for this account")

        logger.info(f"Found {len(transactions)} transactions for account {address}")

        return schemas.AccountTransactionsResponse(transactions=transactions)
    except Exception as e:
        logger.error(f"Error retrieving transactions for account {address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions") from e