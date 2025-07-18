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

class CreateTransactionResponse(BaseModel):
    """Schema for creating a transaction response."""
    message: str
    transaction_hash: str

    model_config = ConfigDict(
        from_attributes=True,
    )

class TransactionIn(BaseModel):
    """Schema for inputting transaction information."""
    from_address: str
    to_address: str
    asset: str
    amount: float
    contract: str | None = None

class TransactionOut(BaseModel):
    """Schema for outputting transaction information."""

    id: int | None = None
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
    transfers: list['TransferResponse'] | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )

class TransferResponse(BaseModel):
    """Schema for transferring assets."""
    asset: str
    from_address: str
    to_address: str
    value: str
    decimals: int

    model_config = ConfigDict(
        from_attributes=True,
    )
class ValidateTransactionResponse(BaseModel):
    """Schema for transaction validation response."""
    hash: str
    tx_type: str | None = None
    is_valid: bool
    reason: str | None = None
    confirmations: int | None = None
    transfers: list[TransferResponse] | None = None

class AccountTransactionsResponse(BaseModel):
    """Schema for account transactions response."""
    transactions: list[TransactionOut]
