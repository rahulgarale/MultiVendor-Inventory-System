from sqlalchemy import Boolean, Column, Integer, Numeric, String, Float, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.db_connection import Base
from app.db.models.stock_vendor_association import stock_vendor_association


class Stocks(Base):
    """Represents a stock item in the inventory, which can be supplied by multiple vendors."""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    vendors = relationship(
        "Vendors", 
        secondary=stock_vendor_association, 
        back_populates="stocks"
    )
    purchase_orders = relationship(
        "PurchaseOrder", 
        back_populates="stock"
    )

    def __repr__(self):
        return f"<Stock(id={self.id}, name={self.name}, sku={self.sku})>"