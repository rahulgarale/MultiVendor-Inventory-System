from sqlalchemy import Boolean, Column, Enum, Integer,DateTime, ForeignKey,Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.db_connection import Base
from sqlalchemy import Enum as SqlEnum
from app.db.status_enum import OrderStatus

class PurchaseOrder(Base):
    """
    Represents a purchase order for a specific stock from a chosen vendor.
    """
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(SqlEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    stock = relationship("Stocks", back_populates="purchase_orders")
    vendor = relationship("Vendors", back_populates="purchase_orders")
    
    def __repr__(self):
        return f"<PurchaseOrder(id={self.id}, stock_id={self.stock_id}, vendor_id={self.vendor_id}, status={self.status})>"