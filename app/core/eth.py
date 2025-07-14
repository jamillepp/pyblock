"""Ethereum wallet and transaction utilities."""

from eth_account import Account
from web3 import Web3
from app.core import config, utils
from app.core.logger import logger
from app.db.schemas import TransactionValidation, Transfer

Account.enable_unaudited_hdwallet_features()


def create_wallet():
    """Create a new Ethereum wallet and return address and private key."""
    acct = Account.create()
    return acct.address, acct.key.hex()


def get_transaction(tx_hash: str):
    """Get transaction and receipt by hash from Sepolia testnet."""
    w3 = config.get_web3_sepolia_provider()
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum provider.")

    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    return tx, receipt

def validate_transaction(tx_data: dict, receipt: dict) -> TransactionValidation:
    """Validate the transaction security."""

    tx_type = None

    if not receipt or receipt.get("status") != 1:
        logger.warning(f"Transaction {tx_data['hash']} failed with status {receipt.status}")
        return TransactionValidation(
            tx_type=tx_type,
            hash=tx_data["hash"].hex(),
            is_valid=False,
            reason="Transaction failed",
            transfers=[]
        )

    transfers: list[Transfer] = []

    if not tx_data["input"] and tx_data["value"] > 0:
        logger.info(f"Transaction {tx_data['hash']} is a simple ETH transfer")
        transfers.append(Transfer(
            asset="ETH",
            to_address=tx_data["to"],
            value=str(utils.from_wei(tx_data["value"]))
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

            transfers.append(Transfer(
                asset=symbol,
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
        return TransactionValidation(
                    tx_type=tx_type,
                    hash=tx_data["hash"].hex(),
                    is_valid=False,
                    reason="No valid ETH or ERC20 transfers found",
                    transfers=[]
                )
    
    logger.info(f"Transaction {tx_data['hash']} is valid with type {tx_type}")

    return TransactionValidation(tx_type=tx_type, hash=tx_data["hash"].hex(), is_valid=True, transfers=transfers)
