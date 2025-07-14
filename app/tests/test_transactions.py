"""Tests for the transactions endpoint of the FastAPI application."""

import os

ETH_TX_HASH = os.getenv("ETH_TX_HASH")
ERC20_TX_HASH = os.getenv("ERC20_TX_HASH")

ACC1_ADDRESS = os.getenv("ACC1_ADDRESS")
ACC2_ADDRESS = os.getenv("ACC2_ADDRESS")

def test_get_eth_transaction(client):
    """Test retrieving a ethereum transaction by hash."""

    response = client.get("/transactions/", params={"tx_hash": ETH_TX_HASH})
    assert response.status_code == 200
    data = response.json()

    assert "hash" in data
    assert data["hash"] == ETH_TX_HASH[2:]
    assert "from_address" in data
    assert "to_address" in data
    assert "value" in data
    assert "gas" in data
    assert "gas_price" in data
    assert "input_data" in data
    assert "receipt_status" in data

def test_get_erc20_transaction(client):
    """Test retrieving an ERC20 transaction by hash."""

    response = client.get("/transactions/", params={"tx_hash": ERC20_TX_HASH})
    assert response.status_code == 200
    data = response.json()

    assert "hash" in data
    assert data["hash"] == ERC20_TX_HASH[2:]
    assert "from_address" in data
    assert "to_address" in data
    assert "value" in data
    assert "gas" in data
    assert "gas_price" in data
    assert "input_data" in data
    assert "receipt_status" in data

def test_validate_eth_transaction(client):
    """Test validating an ethereum transaction."""

    response = client.get("/transactions/validate", params={"tx_hash": ETH_TX_HASH})
    assert response.status_code == 200
    data = response.json()

    assert "hash" in data
    assert data["hash"] == ETH_TX_HASH[2:]
    assert "tx_type" in data
    assert data["tx_type"] == "eth"
    assert "is_valid" in data
    assert data["is_valid"] is True


def test_validate_erc20_transaction(client):
    """Test validating an ERC20 transaction."""

    response = client.get("/transactions/validate", params={"tx_hash": ERC20_TX_HASH})
    assert response.status_code == 200
    data = response.json()

    assert "hash" in data
    assert data["hash"] == ERC20_TX_HASH[2:]
    assert "tx_type" in data
    assert data["tx_type"] == "erc20"
    assert "is_valid" in data
    assert data["is_valid"] is True

def test_crate_eth_transaction(client):
    """Test creating an ethereum transaction."""

    transaction_data = {
        "from_address": ACC1_ADDRESS,
        "to_address": ACC2_ADDRESS,
        "asset": "ETH",
        "amount": 0.01
    }

    response = client.post("/transactions", json=transaction_data)
    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert data["message"] == "Transaction created successfully"
    assert "transaction_hash" in data
