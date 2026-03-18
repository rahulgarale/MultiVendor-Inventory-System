from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.db_connection import Base
from app.db.models.stock_vendor_association import stock_vendor_association

class Vendors(Base):
    """
    Represents a vendor that supplies stock items, with contact information and relationships to stocks and purchase orders.
    """
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    stocks = relationship(
        "Stocks",
        secondary=stock_vendor_association,
        back_populates="vendors"
    )
    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="vendor"
    )
    def __repr__(self):
        return f"<Vendor(id={self.id}, name={self.name})>"
