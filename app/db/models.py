from sqlalchemy import Column, Integer, String

from app.db.session import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    private_key = Column(String, nullable=False)
