from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

class OrderStatus(Enum):
    ACTIVE = "ACTIVE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

@dataclass
class Order:
    id: int
    creator_id: int
    creator_username: str
    currency_from: str
    currency_to: str
    amount: float
    rate: float
    payment_method: str
    execution_time: timedelta  # Срок исполнения
    status: OrderStatus = OrderStatus.ACTIVE
    executor_id: Optional[int] = None
    executor_username: Optional[str] = None
    created_at: datetime = datetime.now() 