from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.models.purchase_orders import PurchaseOrder
from app.core.exceptions import IntegrityException, DatabaseException, PurchaseOrderNotFoundException
from app.core.logging import get_logger
from app.db.status_enum import OrderStatus

logger = get_logger(__name__)

class PurchaseOrderRepository:
    """
    implementation of PurchaseOrderRepository.
    """
    
    VALID_STATUSES = list(OrderStatus)
    VALID_TRANSITIONS = {
        OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
        OrderStatus.CONFIRMED: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
        OrderStatus.DELIVERED: [],
        OrderStatus.CANCELLED: []
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, order: PurchaseOrder) -> PurchaseOrder:
        """
        Create a new purchase order in the database.
        
        Args:
            order: PurchaseOrder model instance
            
        Returns:
            Created PurchaseOrder instance with ID
            
        Raises:
            IntegrityException: If foreign key constraints fail
            DatabaseException: If database operation fails
        """
        try:
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            return order
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating purchase order: {str(e)}")
            raise IntegrityException(f"Invalid stock or vendor reference")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating purchase order: {str(e)}")
            raise DatabaseException(f"Failed to create purchase order: {str(e)}")
    
    def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    def get_all(self, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
        return self.db.query(PurchaseOrder).offset(skip).limit(limit).all()
        
    def get_by_status(self, status: OrderStatus) -> List[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.status == status).all()
        
    def get_by_vendor(self, vendor_id: int) -> List[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.vendor_id == vendor_id).all()
            
    def get_by_stock(self, stock_id: int) -> List[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.stock_id == stock_id).all()
    
    def update(self, order_id: int, order_data: dict) -> Optional[PurchaseOrder]:
        """
        Update purchase order data.
        
        Args:
            order_id: Purchase order ID
            order_data: Dictionary with fields to update
            
        Returns:
            Updated PurchaseOrder instance or None if not found
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                raise PurchaseOrderNotFoundException(order_id)
            
            for key, value in order_data.items():
                if value is not None and hasattr(order, key):
                    setattr(order, key, value)
            
            self.db.commit()
            self.db.refresh(order)
            return order
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating purchase order {order_id}: {str(e)}")
            raise IntegrityException(f"Update violates database constraints")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating purchase order {order_id}: {str(e)}")
            raise DatabaseException(f"Failed to update purchase order: {str(e)}")
    
    def delete(self, order_id: int) -> bool:
        """
        Delete a purchase order by ID.
        
        Args:
            order_id: Purchase order ID
            
        Returns:
            True if order was deleted, False if not found
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                return False
            
            order.is_active = False
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting purchase order {order_id}: {str(e)}")
            raise DatabaseException(f"Failed to delete purchase order: {str(e)}")
    
    def exists(self, order_id: int) -> bool:
        """
        Check if a purchase order exists.
        
        Args:
            order_id: Purchase order ID
            
        Returns:
            True if order exists, False otherwise
        """
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first() is not None
    
    def update_status(self, order_id: int, new_status: OrderStatus) -> Optional[PurchaseOrder]:
        """
        Update purchase order status with validation.
        
        Args:
            order_id: Purchase order ID
            new_status: New status value
            
        Returns:
            Updated PurchaseOrder instance or None if not found
            
        Raises:
            ValueError: If status transition is invalid
        """
        try:
            from app.core.exceptions import InvalidPurchaseOrderStatusException
            
            order = self.get_by_id(order_id)
            if not order:
                raise PurchaseOrderNotFoundException(order_id)
            current_status = order.status

            if not isinstance(new_status, OrderStatus):
                raise ValueError(f"Invalid status: {new_status}")
            
            # Validate transition
            allowed_transitions = self.VALID_TRANSITIONS.get(current_status, [])
            if new_status not in allowed_transitions:
                raise InvalidPurchaseOrderStatusException(current_status, new_status)
            
            order.status = new_status
            self.db.commit()
            self.db.refresh(order)
            return order
        except (ValueError, IntegrityError, SQLAlchemyError) as e:
            self.db.rollback()
            logger.error(f"Error updating purchase order status: {str(e)}")
            raise
