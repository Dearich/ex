from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class UserStatus(Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"

@dataclass
class Order:
    id: str
    creator_id: int
    order_type: OrderType
    amount: float
    rate: float
    currency_from: str
    currency_to: str
    status: OrderStatus
    created_at: datetime
    executor_id: int = None
    completed_at: datetime = None 