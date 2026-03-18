from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.vendors import VendorResponse

class StockBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Stock item name")
    sku: str = Field(..., min_length=1, max_length=100, description="Stock keeping unit")
    description: Optional[str] = Field(None, description="Item description")
    quantity: int = Field(..., ge=0, description="Current quantity in stock")
    unit_price: float = Field(..., gt=0, description="Price per unit")


class StockCreate(StockBase):
    """Schema for creating a new stock item."""
    pass


class StockUpdate(BaseModel):
    """Schema for updating stock data."""
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None


class StockResponse(StockBase):
    """Schema for stock responses without vendor details."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockDetailResponse(StockResponse):
    """Schema for detailed stock response with vendors."""
    vendors: List[VendorResponse] = []
