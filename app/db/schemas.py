from pydantic import BaseModel, ConfigDict

class WalletOut(BaseModel):
    id: int
    address: str

    model_config = ConfigDict(
        from_attributes=True,
    )

class WalletCreateResponse(BaseModel):
    message: str
    addresses: list[str]
