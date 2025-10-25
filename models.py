import csv
import random
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
    longitude: float
    mcc_cd: int

# Transactions
@dataclass
class Transaction:
    transaction_id: Optional[int]
    merchant: Merchant
    client: Client
    transaction_dttm: datetime
    transaction_amt: float
