from pydantic import BaseModel, Field


class StockVendorAssociation(BaseModel):
    """Schema for associating a vendor with a stock."""
    vendor_id: int = Field(..., gt=0, description="Vendor ID to associate")


class VendorListResponse(BaseModel):
    """Schema for listing vendors for a specific stock."""
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True