"""Ethereum wallet and transaction utilities."""

from eth_account import Account
from web3 import Web3
from app.core import config, utils
from app.core.logger import logger
from app.db import schemas

Account.enable_unaudited_hdwallet_features()


def create_wallet():
    """Create a new Ethereum wallet and return address and private key."""
    acct = Account.create()
    private_key = "0x" + acct.key.hex()
    return acct.address, private_key

def create_transaction(transaction: schemas.TransactionIn, private_key: str) -> schemas.TransactionOut:
    """Create a new transaction and return the transaction hash."""
    w3 = config.get_web3_provider()
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum provider.")

    sender = w3.eth.account.from_key(private_key).address
    if Web3.to_checksum_address(sender) != Web3.to_checksum_address(transaction.from_address):
        raise ValueError("Private key does not match from_address")

    value_wei = w3.to_wei(transaction.amount, 'ether')
    balance = w3.eth.get_balance(transaction.from_address)
    if balance < value_wei:
        raise ValueError("Insufficient balance for the transaction")

    gas_price = int(w3.eth.gas_price * 1.2)
    nonce = w3.eth.get_transaction_count(transaction.from_address, 'pending')

    tx = None
    decimals = 18
    if transaction.asset.upper() == "ETH":
        gas_limit = w3.eth.estimate_gas({
            'from': transaction.from_address,
            'to': transaction.to_address,
            'value': value_wei,
        })

        tx = {
            "nonce": nonce,
            "to": Web3.to_checksum_address(transaction.to_address),
            "value": value_wei,
            "gas": gas_limit,
            "gasPrice": gas_price
        }
    else:
        if not transaction.contract:
            raise ValueError("Contract address is required for ERC20 transactions")

        contract = utils.get_token_contract(transaction.contract)
        if not contract:
            raise ValueError("Invalid contract address for ERC20 transaction")

        decimals = contract.functions.decimals().call()

        gas_limit = contract.functions.transfer(transaction.to_address, int(transaction.amount * 10**decimals)).estimate_gas({
            "from": transaction.from_address,
        })

        tx = contract.functions.transfer(transaction.to_address, int(transaction.amount * 10**decimals)).build_transaction({
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
        })

    if not tx:
        raise ValueError("Failed to build transaction")

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        logger.error(f"Transaction failed with status {receipt.status}")
        raise RuntimeError(f"Transaction failed with status {receipt.status}")

    logger.info(f"Transaction {tx_hash.hex()} created successfully")

    return schemas.TransactionOut(
        hash=tx_hash.hex(),
        from_address=transaction.from_address,
        to_address=transaction.to_address,
        value=str(value_wei),
        gas=gas_limit,
        gas_price=gas_price,
        input_data=tx.get("input", ""),
        receipt_status=receipt.status,
        token_contract=transaction.contract,
        token_symbol=transaction.asset.upper(),
        token_decimals=decimals,
        transaction_type="eth" if transaction.asset.upper() == "ETH" else "erc20"
    )

def get_transaction(tx_hash: str):
    """Get transaction and receipt by hash from Sepolia testnet."""
    w3 = config.get_web3_provider()
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum provider.")

    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    return tx, receipt

def validate_transaction(tx_data: dict, receipt: dict) -> schemas.ValidateTransactionResponse:
    """Validate the transaction security."""

    tx_type = None

    if not receipt or receipt.get("status") != 1:
        logger.warning(f"Transaction {tx_data['hash']} failed with status {receipt.status}")
        return schemas.ValidateTransactionResponse(
            tx_type=tx_type,
            hash=tx_data["hash"].hex(),
            is_valid=False,
            reason="Transaction failed",
            transfers=[]
        )

    transfers: list[schemas.TransferResponse] = []

    if not tx_data["input"] and tx_data["value"] > 0:
        logger.info(f"Transaction {tx_data['hash']} is a simple ETH transfer")
        transfers.append(schemas.TransferResponse(
            asset="ETH",
            from_address=tx_data["from"],
            to_address=tx_data["to"],
            value=str(utils.from_wei(tx_data["value"])),
            decimals=18
        ))
        tx_type = "eth"

    for log in receipt["logs"]:
        if log["topics"][0].hex() != utils.get_transfer_event_signature():
            logger.info(f"Log {log['transactionHash'].hex()} is not a transfer event, skipping")
            continue
        try:
            contract_address = log["address"]
            symbol, decimals = utils.get_token_metadata(contract_address)
            to_address = Web3.to_checksum_address("0x" + log["topics"][2].hex()[-40:])

            raw_value = int(log["data"].hex(), 16)
            value = utils.from_wei(raw_value, decimals)

            transfers.append(schemas.TransferResponse(
                asset=symbol,
                from_address=tx_data["from"],
                to_address=to_address,
                value=value,
                decimals=decimals
            ))
            tx_type = "erc20"
        except Exception as e:
            logger.error(f"Error processing transfer log: {e}")
            continue

    if tx_type is None:
        tx_type = "unknown"

    if not transfers:
        logger.warning(f"Transaction {tx_data['hash']} has no valid ETH or ERC20 transfers")
        return schemas.ValidateTransactionResponse(
                    tx_type=tx_type,
                    hash=tx_data["hash"].hex(),
                    is_valid=False,
                    reason="No valid ETH or ERC20 transfers found",
                    transfers=[]
                )

    logger.info(f"Transaction {tx_data['hash']} is valid with type {tx_type}")

    return schemas.ValidateTransactionResponse(tx_type=tx_type, hash=tx_data["hash"].hex(), is_valid=True, transfers=transfers)
