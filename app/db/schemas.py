"""Schemas for the application using Pydantic."""

from pydantic import BaseModel, ConfigDict

class WalletOut(BaseModel):
    """Schema for outputting wallet information."""
    id: int
    address: str

    model_config = ConfigDict(
        from_attributes=True,
    )

class WalletCreateResponse(BaseModel):
    """Schema for wallet creation response."""
    message: str
    addresses: list[str]

class TransactionOut(BaseModel):
    """Schema for outputting transaction information."""

    id: int
    hash: str
    from_address: str
    to_address: str | None = None
    value: str
    gas: int
    gas_price: int
    input_data: str | None = None
    receipt_status: int
    token_contract: str | None = None
    token_symbol: str | None = None
    token_decimals: int | None = None
    transaction_type: str

    model_config = ConfigDict(
        from_attributes=True,
    )

class Transfer(BaseModel):
    """Schema for transferring assets."""
    asset: str | None = None
    to_address: str | None = None
    value: str | None = None
    decimals: int | None = None
class TransactionValidation(BaseModel):
    """Schema for transaction validation response."""
    hash: str
    tx_type: str = "eth"
    is_valid: bool
    reason: str | None = None
    confirmations: int | None = None
    transfers: list[Transfer] | None = None
