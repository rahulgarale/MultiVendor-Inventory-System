from typing import List, Optional
from app.db.models.stocks import Stocks
from app.schemas.stocks import StockCreate, StockUpdate
from app.repositories.stocks_repository import StockRepository
from app.core.exceptions import (
    StockNotFoundException,
    StockAlreadyExistsException,
    InsufficientStockException,
    InvalidVendorDataException,
)

class StockService:
    def __init__(self, repository: StockRepository):
        self.repository = repository
    
    def create(self, stock: StockCreate) -> Stocks:
        self._validate_stock_data(stock)
        
        # Check for duplicate SKU
        existing_by_sku = self.repository.get_by_sku(stock.sku)
        if existing_by_sku:
            raise StockAlreadyExistsException(stock.sku)
        
        # Check for duplicate name
        existing_by_name = self.repository.get_by_name(stock.name)
        if existing_by_name:
            raise StockAlreadyExistsException(stock.name)
        
        stock_model = Stocks(
            name=stock.name,
            sku=stock.sku,
            description=stock.description,
            quantity=stock.quantity,
            unit_price=stock.unit_price,
            is_active=True
        )
        
        return self.repository.create(stock_model)
    
    def get_by_id(self, stock_id: int) -> Optional[Stocks]:
       return self.repository.get_by_id(stock_id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Stocks]:
        if limit > 1000:
            limit = 1000
        if skip < 0:
            skip = 0
        return self.repository.get_all(skip=skip, limit=limit)
    
    def update(self, stock_id: int, stock_update: StockUpdate) -> Stocks:
        stock = self.repository.get_by_id(stock_id)
        if not stock:
            raise StockNotFoundException(stock_id)
        
        update_data = stock_update.model_dump(exclude_unset=True)
        
        if "unit_price" in update_data and update_data["unit_price"]:
            self._validate_price(update_data["unit_price"])
        
        if "quantity" in update_data and update_data["quantity"] is not None:
            self._validate_quantity(update_data["quantity"])
        
        if "name" in update_data and update_data["name"]:
            if update_data["name"] != stock.name:
                existing_name = self.repository.get_by_name(update_data["name"])
                if existing_name:
                    raise StockAlreadyExistsException(update_data["name"])
        
        return self.repository.update(stock_id, update_data)
    
    def delete(self, stock_id: int) -> bool:
        if not self.repository.exists(stock_id):
            raise StockNotFoundException(stock_id)
        
        self.repository.delete(stock_id)
        return True
    
    def adjust_quantity(self, stock_id: int, quantity_change: int) -> Stocks:
        stock = self.repository.get_by_id(stock_id)
        if not stock:
            raise StockNotFoundException(stock_id)
        
        # Check if we have enough stock for negative adjustments
        if quantity_change < 0 and (stock.quantity + quantity_change) < 0:
            raise InsufficientStockException(stock_id, abs(quantity_change), stock.quantity)
        
        return self.repository.update_quantity(stock_id, quantity_change)
    
    # Validation Methods
    def _validate_stock_data(self, stock: StockCreate) -> None:
        self._validate_name(stock.name)
        self._validate_sku(stock.sku)
        self._validate_quantity(stock.quantity)
        self._validate_price(stock.unit_price)
    
    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise InvalidVendorDataException("Stock name cannot be empty", "name")
        if len(name) < 2:
            raise InvalidVendorDataException("Stock name must be at least 2 characters", "name")
        if len(name) > 255:
            raise InvalidVendorDataException("Stock name must not exceed 255 characters", "name")
    
    @staticmethod
    def _validate_sku(sku: str) -> None:
        if not sku or not sku.strip():
            raise InvalidVendorDataException("SKU cannot be empty", "sku")
        if len(sku) < 1:
            raise InvalidVendorDataException("SKU must be at least 1 character", "sku")
        if len(sku) > 100:
            raise InvalidVendorDataException("SKU must not exceed 100 characters", "sku")
    
    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity < 0:
            raise InvalidVendorDataException("Quantity cannot be negative", "quantity")
    
    @staticmethod
    def _validate_price(price: float) -> None:
        if price <= 0:
            raise InvalidVendorDataException("Unit price must be greater than zero", "unit_price")
        if price > 999999.99:
            raise InvalidVendorDataException("Unit price exceeds maximum allowed value", "unit_price")
    
    def add_vendor(self, stock_id: int, vendor_id: int) -> None:
        stock = self.repository.get_by_id(stock_id)
        if not stock:
            raise StockNotFoundException(stock_id)
        
        self.repository.add_vendor(stock_id, vendor_id)
    
    def remove_vendor(self, stock_id: int, vendor_id: int) -> None:
        stock = self.repository.get_by_id(stock_id)
        if not stock:
            raise StockNotFoundException(stock_id)
        
        self.repository.remove_vendor(stock_id, vendor_id)
    
    def get_vendors(self, stock_id: int) -> List:
        stock = self.repository.get_by_id(stock_id)
        if not stock:
            raise StockNotFoundException(stock_id)    
        return self.repository.get_vendors(stock_id)
        