from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.stocks import StockResponse
from app.schemas.vendors import VendorResponse


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase order data."""
    stock_id: int = Field(..., gt=0, description="Stock item ID")
    vendor_id: int = Field(..., gt=0, description="Vendor ID")
    quantity: int = Field(..., gt=0, description="Order quantity")
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a new purchase order."""
    pass


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating purchase order."""
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order responses."""
    id: int
    status: str
    order_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    """Schema for detailed purchase order with stock and vendor info."""
    stock: Optional[StockResponse] = None
    vendor: Optional[VendorResponse] = None