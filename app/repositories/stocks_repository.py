from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.models.stocks import Stocks
from app.core.exceptions import IntegrityException, DatabaseException, StockNotFoundException
from app.core.logging import get_logger

logger = get_logger(__name__)

class StockRepository:
    """
    Repository for stock database operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, stock: Stocks) -> Stocks:
        """
        Create a new stock item in the database.
        
        Args:
            stock: Stocks model instance
            
        Returns:
            Created Stocks instance with ID
            
        Raises:
            IntegrityException: If stock with same SKU or name exists
            DatabaseException: If database operation fails
        """
        try:
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
            return stock
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating stock: {str(e)}")
            raise IntegrityException(f"Stock with this SKU or name already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating stock: {str(e)}")
            raise DatabaseException(f"Failed to create stock: {str(e)}")
    
    def get_by_id(self, stock_id: int) -> Optional[Stocks]:
        return self.db.query(Stocks).filter(Stocks.id == stock_id).first()
        
    def get_by_sku(self, sku: str) -> Optional[Stocks]:
        return self.db.query(Stocks).filter(Stocks.sku == sku).first()
        
    def get_by_name(self, name: str) -> Optional[Stocks]:
        return self.db.query(Stocks).filter(Stocks.name == name).first()
        
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Stocks]:
        return self.db.query(Stocks).offset(skip).limit(limit).all()
        
    def update(self, stock_id: int, stock_data: dict) -> Optional[Stocks]:
        """
        Update stock data.
        
        Args:
            stock_id: Stock ID
            stock_data: Dictionary with fields to update
            
        Returns:
            Updated Stocks instance or None if not found
        """
        try:
            stock = self.get_by_id(stock_id)
            if not stock:
                raise StockNotFoundException(stock_id)
            
            for key, value in stock_data.items():
                if value is not None and hasattr(stock, key):
                    setattr(stock, key, value)
            
            self.db.commit()
            self.db.refresh(stock)
            return stock
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating stock {stock_id}: {str(e)}")
            raise IntegrityException(f"Update violates database constraints")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating stock {stock_id}: {str(e)}")
            raise DatabaseException(f"Failed to update stock: {str(e)}")
    
    def delete(self, stock_id: int) -> bool:
        """
        Delete a stock by ID.
        
        Args:
            stock_id: Stock ID
            
        Returns:
            True if stock was deleted, False if not found
        """
        try:
            stock = self.get_by_id(stock_id)
            if not stock:
                return False
            stock.is_active = False
            self.db.commit()
            self.db.refresh(stock)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting stock {stock_id}: {str(e)}")
            raise DatabaseException(f"Failed to delete stock: {str(e)}")
    
    def exists(self, stock_id: int) -> bool:
        """
        Check if a stock exists.
        
        Args:
            stock_id: Stock ID
            
        Returns:
            True if stock exists, False otherwise
        """
        return self.db.query(Stocks).filter(Stocks.id == stock_id).first() is not None
    
    def update_quantity(self, stock_id: int, quantity_change: int) -> Optional[Stocks]:
        """
        Update stock quantity by delta (positive or negative).
        
        Args:
            stock_id: Stock ID
            quantity_change: Change in quantity (+ or -)
            
        Returns:
            Updated Stocks instance or None if not found
        """
        try:
            stock = self.get_by_id(stock_id)
            if not stock:
                raise StockNotFoundException(stock_id)
        
            stock.quantity += quantity_change
            
            if stock.quantity < 0:
                stock.quantity = 0
            
            self.db.commit()
            self.db.refresh(stock)
            return stock
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating stock quantity {stock_id}: {str(e)}")
            raise DatabaseException(f"Failed to update stock quantity: {str(e)}")
    
    def add_vendor(self, stock_id: int, vendor_id: int) -> None:
        """
        Associate a vendor with a stock as an approved supplier.
        
        Args:
            stock_id: Stock ID
            vendor_id: Vendor ID
            
        Raises:
            DatabaseException: If operation fails
        """
        try:
            from app.db.models.vendors import Vendors
            
            stock = self.get_by_id(stock_id)
            if not stock:
                raise DatabaseException(f"Stock with ID {stock_id} not found")
            
            vendor = self.db.query(Vendors).filter(Vendors.id == vendor_id).first()
            if not vendor:
                raise DatabaseException(f"Vendor with ID {vendor_id} not found")
            
            # Check if vendor already associated
            if vendor in stock.vendors:
                return
            
            stock.vendors.append(vendor)
            self.db.commit()
        except DatabaseException:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error associating vendor {vendor_id} with stock {stock_id}: {str(e)}")
            raise DatabaseException(f"Failed to associate vendor with stock: {str(e)}")
    
    def remove_vendor(self, stock_id: int, vendor_id: int) -> None:
        """
        Disassociate a vendor from a stock.
        
        Args:
            stock_id: Stock ID
            vendor_id: Vendor ID
            
        Raises:
            DatabaseException: If operation fails
        """
        try:
            from app.db.models.vendors import Vendors
            
            stock = self.get_by_id(stock_id)
            if not stock:
                raise DatabaseException(f"Stock with ID {stock_id} not found")
            
            vendor = self.db.query(Vendors).filter(Vendors.id == vendor_id).first()
            if not vendor:
                raise DatabaseException(f"Vendor with ID {vendor_id} not found")
            
            if vendor in stock.vendors:
                stock.vendors.remove(vendor)
                self.db.commit()
        except DatabaseException:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error removing vendor {vendor_id} from stock {stock_id}: {str(e)}")
            raise DatabaseException(f"Failed to remove vendor from stock: {str(e)}")
    
    def get_vendors(self, stock_id: int) -> List:
        stock = self.get_by_id(stock_id)
        if not stock:
            raise DatabaseException(f"Stock with ID {stock_id} not found")
        return stock.vendors
