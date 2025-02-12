from typing import List, Dict, Optional
from models.order import Order, OrderStatus, UserStatus

class Storage:
    _orders: Dict[int, Order] = {}
    _last_order_id: int = 0
    _verified_users: set[int] = set()  # Множество ID проверенных пользователей

    @classmethod
    def create_order(cls, **kwargs) -> Order:
        cls._last_order_id += 1
        order = Order(id=cls._last_order_id, **kwargs)
        cls._orders[order.id] = order
        return order

    @classmethod
    def get_user_orders(cls, user_id: int) -> List[Order]:
        return [order for order in cls._orders.values() 
                if order.creator_id == user_id and order.status != OrderStatus.CANCELLED]

    @classmethod
    def get_available_orders(cls, currency_from: Optional[str] = None, 
                           currency_to: Optional[str] = None) -> List[Order]:
        orders = [order for order in cls._orders.values() 
                 if order.status == OrderStatus.ACTIVE]
        
        if currency_from:
            orders = [o for o in orders if o.currency_from == currency_from]
        if currency_to:
            orders = [o for o in orders if o.currency_to == currency_to]
        
        return orders

    @classmethod
    def get_order(cls, order_id: int) -> Optional[Order]:
        return cls._orders.get(order_id)

    @classmethod
    def update_order(cls, order_id: int, **kwargs) -> Optional[Order]:
        if order := cls._orders.get(order_id):
            for key, value in kwargs.items():
                setattr(order, key, value)
            return order
        return None

    @classmethod
    def get_user_status(cls, user_id: int) -> UserStatus:
        return UserStatus.VERIFIED if user_id in cls._verified_users else UserStatus.UNVERIFIED 