from pydantic import BaseModel, Field
from datetime import datetime


class VendorBase(BaseModel):
    """Base schema for vendor data."""
    name: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    email: str = Field(..., description="Vendor email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Contact phone number")
    address: str = Field(..., min_length=1, description="Vendor address")

class VendorCreate(VendorBase):
    """Schema for creating a new vendor."""
    pass

class VendorUpdate(VendorBase):
    """Schema for updating an existing vendor."""
    name: str = Field(None, min_length=1, max_length=255, description="Vendor name")
    email: str = None
    phone: str = None
    address: str = None
    is_active: bool = Field(None, description="Indicates if the vendor is active (true=active, false=inactive)")

class VendorResponse(VendorBase):
    """Schema for vendor response data."""
    id: int = Field(..., description="Unique identifier for the vendor")
    is_active: bool = Field(..., description="Indicates if the vendor is active (true=active, false=inactive)")
    created_at: datetime = Field(..., description="Timestamp when the vendor was created")
    updated_at: datetime = Field(..., description="Timestamp when the vendor was last updated")

    class Config:
        from_attributes = True
