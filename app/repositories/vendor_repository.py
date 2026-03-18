from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.models.vendors import Vendors
from app.core.exceptions import IntegrityException, DatabaseException, VendorAlreadyExistsException, VendorNotFoundException
from app.core.logging import get_logger

logger = get_logger(__name__)

class VendorRepository:
    """
    Repository for vendor database operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, vendor: Vendors) -> Vendors:
        """
        Create a new vendor in the database.
        
        Args:
            vendor: Vendors model instance
            
        Returns:
            Created Vendors instance with ID
            
        Raises:
            IntegrityException: If vendor with same name or email exists
            DatabaseException: If database operation fails
        """
        try:
            self.db.add(vendor)
            self.db.commit()
            self.db.refresh(vendor)
            return vendor
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating vendor: {str(e)}")
            raise IntegrityException(f"Vendor with this name or email already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating vendor: {str(e)}")
            raise DatabaseException(f"Failed to create vendor: {str(e)}")
    
    def get_by_id(self, vendor_id: int) -> Optional[Vendors]:
        return self.db.query(Vendors).filter(Vendors.id == vendor_id).first()
    
    def get_by_name(self, name: str) -> Optional[Vendors]:
        return self.db.query(Vendors).filter(Vendors.name == name).first()
    
    def get_by_email(self, email: str) -> Optional[Vendors]:
        return self.db.query(Vendors).filter(Vendors.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Vendors]:
        if limit > 1000:
            limit = 1000
        if skip < 0:
            skip = 0
        return self.db.query(Vendors).offset(skip).limit(limit).all()
    
    def get_active(self) -> List[Vendors]:
        return self.db.query(Vendors).filter(Vendors.is_active == True).all()
    
    def update(self, vendor_id: int, vendor_data: dict) -> Optional[Vendors]:
        """
        Update vendor data.
        
        Args:
            vendor_id: Vendor ID
            vendor_data: Dictionary with fields to update
            
        Returns:
            Updated Vendors instance or None if not found
            
        Raises:
            IntegrityException: If update violates constraints
            DatabaseException: If database operation fails
        """
        try:
            vendor = self.get_by_id(vendor_id)
            for key, value in vendor_data.items():
                if value is not None and hasattr(vendor, key):
                    setattr(vendor, key, value)
            
            self.db.commit()
            self.db.refresh(vendor)
            return vendor
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating vendor {vendor_id}: {str(e)}")
            raise IntegrityException(f"Update violates database constraints")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating vendor {vendor_id}: {str(e)}")
            raise DatabaseException(f"Failed to update vendor: {str(e)}")
    
    def delete(self, vendor_id: int) -> bool:
        """
        Delete a vendor by ID.
        
        Args:
            vendor_id: Vendor ID
            
        Returns:
            True if vendor was deleted, False if not found
            
        Raises:
            DatabaseException: If database operation fails
        """
        try:
            vendor = self.get_by_id(vendor_id)
            if not vendor:
                return False
            vendor.is_active = False
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting vendor {vendor_id}: {str(e)}")
            raise DatabaseException(f"Failed to delete vendor: {str(e)}")
    
    def exists(self, vendor_id: int) -> bool:
        """
        Check if a vendor exists.
        
        Args:
            vendor_id: Vendor ID
            
        Returns:
            True if vendor exists, False otherwise
        """
        return self.db.query(Vendors).filter(Vendors.id == vendor_id).first() is not None
