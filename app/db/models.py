"""Database models for the application using SQLAlchemy."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Wallet(Base):
    """Model representing a cryptocurrency wallet."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    private_key = Column(String, nullable=False)

class Transaction(Base):
    """Model representing a cryptocurrency transaction (ETH or ERC20)."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String, unique=True, index=True, nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=True)
    value = Column(String, nullable=False)
    gas = Column(Integer, nullable=False)
    gas_price = Column(Integer, nullable=False)
    input_data = Column(String, nullable=True)
    receipt_status = Column(Integer, nullable=False)
    token_contract = Column(String, nullable=True)
    token_symbol = Column(String, nullable=True)
    token_decimals = Column(Integer, nullable=True)
    transaction_type = Column(String, nullable=False, default="eth")

    transfers= relationship("Transfer", back_populates="transaction")

class Transfer(Base):
    """Model representing a token transfer."""
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    asset = Column(String, nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    value = Column(String, nullable=False)
    decimals = Column(Integer, nullable=False)

    transaction = relationship("Transaction", back_populates="transfers")
