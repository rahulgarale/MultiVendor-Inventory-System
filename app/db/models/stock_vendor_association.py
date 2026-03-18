
from sqlalchemy import Column, ForeignKey, Integer, Table
from app.db.db_connection import Base

stock_vendor_association =Table(
    'stock_vendor_association',
    Base.metadata,
    Column('stock_id', Integer, ForeignKey('stocks.id', ondelete='CASCADE'), primary_key=True),
    Column('vendor_id', Integer, ForeignKey('vendors.id', ondelete='CASCADE'), primary_key=True)
)