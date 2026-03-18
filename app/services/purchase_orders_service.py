from typing import List, Optional

from app.db.models.purchase_orders import PurchaseOrder
from app.db.status_enum import OrderStatus
from app.schemas.Purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate
from app.repositories.purchase_orders_repository import PurchaseOrderRepository
from app.core.exceptions import (
    PurchaseOrderNotFoundException,
    PurchaseOrderOperationException,
    InvalidVendorDataException,
)

class PurchaseOrderService:
    
    def __init__(self, repository: PurchaseOrderRepository, stock_repository=None, vendor_repository=None):
        self.repository = repository
        self.stock_repository = stock_repository
        self.vendor_repository = vendor_repository
    
    def create(self, order: PurchaseOrderCreate) -> PurchaseOrder:
        self._validate_order_data(order)

        if self.stock_repository:
            stock = self.stock_repository.get_by_id(order.stock_id)
            if not stock:
                raise PurchaseOrderOperationException(f"Stock with ID {order.stock_id} not found")
            if not stock.is_active:
                raise PurchaseOrderOperationException(f"Stock with ID {order.stock_id} is not active")

        if self.vendor_repository:
            vendor = self.vendor_repository.get_by_id(order.vendor_id)
            if not vendor:
                raise PurchaseOrderOperationException(f"Vendor with ID {order.vendor_id} not found")
            if not vendor.is_active:
                raise PurchaseOrderOperationException(f"Vendor with ID {order.vendor_id} is not active")

            stock = self.stock_repository.get_by_id(order.stock_id)
            if stock:
                approved_vendor_ids = [v.id for v in stock.vendors if v.is_active]
                if order.vendor_id not in approved_vendor_ids:
                    raise PurchaseOrderOperationException(
                        f"Vendor {order.vendor_id} is not an approved supplier for stock {order.stock_id}"
                    )

                if order.quantity > stock.quantity:
                    raise PurchaseOrderOperationException(
                        f"Insufficient stock. Requested: {order.quantity}, Available: {stock.quantity}"
                    )

        order_model = PurchaseOrder(
            stock_id=order.stock_id,
            vendor_id=order.vendor_id,
            quantity=order.quantity,
            notes=order.notes,
            status=OrderStatus.PENDING
        )

        return self.repository.create(order_model)
    
    def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        return self.repository.get_by_id(order_id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
        if limit > 1000:
            limit = 1000
        if skip < 0:
            skip = 0
        return self.repository.get_all(skip=skip, limit=limit)
    
    def get_by_status(self, status: str) -> List[PurchaseOrder]:
        try:
            status_enum = OrderStatus(status)
        except ValueError:
            raise PurchaseOrderOperationException(f"Invalid status: {status}. Valid: {[s.value for s in OrderStatus]}")
        return self.repository.get_by_status(status_enum)

    def get_by_vendor(self, vendor_id: int) -> List[PurchaseOrder]:
        return self.repository.get_by_vendor(vendor_id)
    
    def get_by_stock(self, stock_id: int) -> List[PurchaseOrder]:
        return self.repository.get_by_stock(stock_id)
    
    def update(self, order_id: int, order_update: PurchaseOrderUpdate) -> PurchaseOrder:
        order = self.repository.get_by_id(order_id)
        if not order:
            raise PurchaseOrderNotFoundException(order_id)
        update_data = order_update.model_dump(exclude_unset=True)
        updated_order = self.repository.update(order_id, update_data)
        return updated_order
        
    def delete(self, order_id: int) -> bool:
        order = self.repository.get_by_id(order_id)
        if not order:
            raise PurchaseOrderNotFoundException(order_id)

        if order.status != OrderStatus.PENDING:
            raise PurchaseOrderOperationException(
                f"Cannot delete order in '{order.status}' status"
            )

        self.repository.delete(order_id)
        return True
    
    def update_status(self, order_id: int, new_status: str) -> PurchaseOrder:
        order = self.get_by_id(order_id)
        if not order:
            raise PurchaseOrderNotFoundException(order_id)
        try:
            new_status_enum = OrderStatus(new_status)
        except ValueError:
            raise PurchaseOrderOperationException(f"Invalid status: {new_status}. Valid: {[s.value for s in OrderStatus]}")

        if new_status_enum == OrderStatus.CONFIRMED and order.status != OrderStatus.CONFIRMED:
            if self.stock_repository:
                all_pending = self.repository.get_by_status(OrderStatus.PENDING)

                earlier_pending_orders = [
                    o for o in all_pending
                    if o.stock_id == order.stock_id
                    and o.id != order_id
                    and o.created_at < order.created_at
                ]

                if earlier_pending_orders:
                    raise PurchaseOrderOperationException(
                        f"Earlier orders {[o.id for o in earlier_pending_orders]} must be confirmed first"
                    )

                stock = self.stock_repository.get_by_id(order.stock_id)
                if not stock or stock.quantity < order.quantity:
                    raise PurchaseOrderOperationException(
                        f"Insufficient stock. Available: {stock.quantity if stock else 0}"
                    )

                self.stock_repository.update(
                    order.stock_id,
                    {"quantity": stock.quantity - order.quantity}
                )

        if new_status_enum == OrderStatus.CANCELLED and order.status == OrderStatus.CONFIRMED:
            if self.stock_repository:
                stock = self.stock_repository.get_by_id(order.stock_id)
                if stock:
                    self.stock_repository.update(
                        order.stock_id,
                        {"quantity": stock.quantity + order.quantity}
                    )

        return self.repository.update_status(order_id, new_status_enum)
    
    def _validate_order_data(self, order: PurchaseOrderCreate) -> None:
        self._validate_stock_id(order.stock_id)
        self._validate_vendor_id(order.vendor_id)
        self._validate_quantity(order.quantity)
    
    @staticmethod
    def _validate_stock_id(stock_id: int) -> None:
        if stock_id <= 0:
            raise InvalidVendorDataException("Stock ID must be a positive integer", "stock_id")
    
    @staticmethod
    def _validate_vendor_id(vendor_id: int) -> None:
        if vendor_id <= 0:
            raise InvalidVendorDataException("Vendor ID must be a positive integer", "vendor_id")
    
    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity <= 0:
            raise InvalidVendorDataException("Quantity must be greater than zero", "quantity")
        if quantity > 1000000:
            raise InvalidVendorDataException("Quantity exceeds maximum allowed value", "quantity")
