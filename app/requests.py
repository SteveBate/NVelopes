from typing import Optional, List
from pydantic import BaseModel

class NewAccountRequest(BaseModel):    
    name: str
    opening_balance: float
    can_go_negative: Optional[bool] = True

class NewUserRequest(BaseModel):
    full_name: str
    username: str
    email: str    
    password: str

class AddEnvelopesRequest(BaseModel):
    account_id: str
    envelopes: list

class AddEnvelopeRequest(BaseModel):
    account_id: str
    envelope: str    

class RenameEnvelopesRequest(BaseModel):
    account_id: str
    envelope_id: int
    new_name: str

class MoveMoneyRequest(BaseModel):
    account_id: str
    from_id: int
    to_id: int
    description: str
    amount: float

class DepositMoneyRequest(BaseModel):
    account_id: str
    envelope_id: int
    description: str
    amount: float

class DebitMoneyRequest(BaseModel):
    account_id: str
    envelope_id: int
    description: str
    amount: float    

class CorrectionRequest(BaseModel):
    account_id: str
    tx_id: int
    description: str
    amount: float

class PaymentSourceRequest(BaseModel):
    envelope_id: int
    amount: float

class AddPaymentSourceRequest(BaseModel):
    account_id: str
    payer: str
    amount: float
    payments: List[PaymentSourceRequest]

class UpdatePaymentSourceRequest(BaseModel):
    account_id: str
    payment_source_id: int
    payer: str
    amount: float
    payments: List[PaymentSourceRequest]

class PayRequest(BaseModel):
    account_id: str
    payment_source_id: int
    payer: str
    amount: float
    description: str
    payments: List[PaymentSourceRequest]

class UndoRequest(BaseModel):
    account_id: str