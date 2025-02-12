from typing import List, Optional
from models.order import Order, OrderStatus
from datetime import timedelta

class OrderService:
    _orders: List[Order] = []
    _last_order_id: int = 0

    @classmethod
    def create_order(cls, **kwargs) -> Order:
        cls._last_order_id += 1
        order = Order(id=cls._last_order_id, **kwargs)
        cls._orders.append(order)
        return order

    @classmethod
    def get_user_orders(cls, user_id: int) -> List[Order]:
        """Получение заявок пользователя (как создателя, так и исполнителя)"""
        return [
            order for order in cls._orders 
            if (order.creator_id == user_id or order.executor_id == user_id)
            and order.status != OrderStatus.CANCELLED
        ]

    @classmethod
    def get_available_orders(cls, currency_from: Optional[str] = None, 
                           currency_to: Optional[str] = None) -> List[Order]:
        """Получение доступных заявок (только в статусе ACTIVE)"""
        orders = [order for order in cls._orders 
                 if order.status == OrderStatus.ACTIVE]
        
        if currency_from:
            orders = [o for o in orders if o.currency_from == currency_from]
        if currency_to:
            orders = [o for o in orders if o.currency_to == currency_to]
        
        return orders

    @classmethod
    def get_order(cls, order_id: int) -> Optional[Order]:
        """Получение заявки по ID"""
        for order in cls._orders:
            if order.id == order_id:
                return order
        return None

    @classmethod
    def update_order(cls, order_id: int, **kwargs) -> Optional[Order]:
        """Обновление заявки"""
        if order := cls.get_order(order_id):
            for key, value in kwargs.items():
                setattr(order, key, value)
            return order
        return None 