from pydantic import BaseModel

class WalletOut(BaseModel):
    id: int
    address: str

    class Config:
        orm_mode = True

class WalletCreateResponse(BaseModel):
    message: str
    addresses: list[str]
