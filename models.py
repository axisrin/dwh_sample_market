from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Client
@dataclass
class Client:
    client_id: int
    gender: str
    age: int

# Store Point
@dataclass
class Merchant:
    merchant_id: int
    latitude: float
    longtitude: float
    mcc_cd: int

# Transactions
@dataclass
class Transaction:
    transaction_id: Optional[int]
    merchant_id: int
    client_id: int
    transaction_dttm: datetime
    transaction_amt: float
