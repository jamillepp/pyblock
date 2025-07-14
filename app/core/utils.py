"""Aplication utility functions."""

import base64
from Crypto.Cipher import AES
from app.core import config


def encrypt_private_key(private_key_hex: str) -> str:
    """Encrypt the private key using AES encryption."""
    if not private_key_hex.startswith("0x"):
        raise ValueError("Private key must start with 0x")

    aes_key = bytes.fromhex(config.AES_KEY)
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(bytes.fromhex(private_key_hex[2:]))
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt_private_key(encrypted_key: str) -> str:
    """Decrypt the private key using AES decryption."""
    aes_key = bytes.fromhex(config.AES_KEY)
    encrypted_data = base64.b64decode(encrypted_key)

    nonce, tag, ciphertext = encrypted_data[:16], encrypted_data[16:32], encrypted_data[32:]
    cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    decrypted_key = cipher.decrypt_and_verify(ciphertext, tag)

    if len(decrypted_key) != 32:
        raise ValueError("Invalid decrypted private key length")

    return "0x" + decrypted_key.hex()

def get_token_metadata(contract_address: str) -> tuple[str, int]:
    """Get token metadata (symbol and decimals) from the contract address."""

    w3 = config.get_web3_sepolia_provider()
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum provider.")

    abi = [
        {"name": "symbol", "outputs": [{"type": "string"}], "inputs": [], "stateMutability": "view", "type": "function"},
        {"name": "decimals", "outputs": [{"type": "uint8"}], "inputs": [], "stateMutability": "view", "type": "function"},
    ]
    contract = w3.eth.contract(address=contract_address, abi=abi)
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    return symbol, decimals

def from_wei(value: int, decimals: int = 18) -> str:
    """Convert value from wei to a human-readable format."""
    return str(value / 10**decimals)

def get_transfer_event_signature() -> str:
    """Get the signature for the ERC20 Transfer event."""

    w3 = config.get_web3_sepolia_provider()
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum provider.")

    return w3.keccak(text="Transfer(address,address,uint256)").hex()

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]

def get_token_contract(token_address: str):
    """Get the token contract instance for the given address."""

    w3 = config.get_web3_sepolia_provider()
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum provider.")

    token_address = w3.to_checksum_address(token_address)
    return w3.eth.contract(address=token_address, abi=ERC20_ABI)
