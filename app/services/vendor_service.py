from typing import List, Optional
import re
from app.db.models.vendors import Vendors
from app.schemas.vendors import VendorCreate, VendorUpdate
from app.repositories.vendor_repository import VendorRepository
from app.core.exceptions import (
    VendorNotFoundException,
    VendorAlreadyExistsException,
    InvalidVendorDataException,
    EmailValidationException,
    PhoneValidationException
)

class VendorService:
    def __init__(self, repository: VendorRepository):
        self.repository = repository
    
    def create(self, vendor: VendorCreate) -> Vendors:
        self._validate_vendor_data(vendor)
        
        existing_by_name = self.repository.get_by_name(vendor.name)
        if existing_by_name:
            raise VendorAlreadyExistsException("name", vendor.name)
        
        existing_by_email = self.repository.get_by_email(vendor.email)
        if existing_by_email:
            raise VendorAlreadyExistsException("email", vendor.email)
        
        vendor_model = Vendors(
            name=vendor.name,
            email=vendor.email,
            phone=vendor.phone,
            address=vendor.address
        )
        
        return self.repository.create(vendor_model)
    
    def get_by_id(self, vendor_id: int) -> Optional[Vendors]:
        return self.repository.get_by_id(vendor_id)
        
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Vendors]:
        return self.repository.get_all(skip=skip, limit=limit)
    
    def get_active(self) -> List[Vendors]:
        return self.repository.get_active()
    
    def update(self, vendor_id: int, vendor_update: VendorUpdate) -> Vendors:
        vendor = self.repository.get_by_id(vendor_id)
        if not vendor:
            raise VendorNotFoundException(vendor_id)
        
        # Validate update data
        update_data = vendor_update.model_dump(exclude_unset=True)
        
        # Validate email if provided
        if "email" in update_data and update_data["email"]:
            if update_data["email"] != vendor.email:
                existing_email = self.repository.get_by_email(update_data["email"])
                if existing_email:
                    raise VendorAlreadyExistsException("email", update_data["email"])
            self._validate_email(update_data["email"])
        
        # Validate name if provided
        if "name" in update_data and update_data["name"]:
            if update_data["name"] != vendor.name:
                existing_name = self.repository.get_by_name(update_data["name"])
                if existing_name:
                    raise VendorAlreadyExistsException("name", update_data["name"])
        
        # Validate phone if provided
        if "phone" in update_data and update_data["phone"]:
            self._validate_phone(update_data["phone"])
        
        # Update vendor
        return self.repository.update(vendor_id, update_data)
    
    def delete(self, vendor_id: int) -> bool:
        if not self.repository.exists(vendor_id):
            raise VendorNotFoundException(vendor_id)
        
        self.repository.delete(vendor_id)
        return True
    
    def _validate_vendor_data(self, vendor: VendorCreate) -> None:
        self._validate_name(vendor.name)
        self._validate_email(vendor.email)
        self._validate_phone(vendor.phone)
        self._validate_address(vendor.address)
    
    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise InvalidVendorDataException("Vendor name cannot be empty", "name")
        if len(name) < 2:
            raise InvalidVendorDataException("Vendor name must be at least 2 characters", "name")
        if len(name) > 255:
            raise InvalidVendorDataException("Vendor name must not exceed 255 characters", "name")
    
    @staticmethod
    def _validate_email(email: str) -> None:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise EmailValidationException(email)
    
    @staticmethod
    def _validate_phone(phone: str) -> None:
        phone_pattern = r'^\+?1?\d{9,15}$'
        phone_clean = re.sub(r'[\s\-\(\)]+', '', phone)
        if not re.match(phone_pattern, phone_clean):
            raise PhoneValidationException(phone)
    
    @staticmethod
    def _validate_address(address: str) -> None:
        if not address or not address.strip():
            raise InvalidVendorDataException("Address cannot be empty", "address")
        if len(address) < 5:
            raise InvalidVendorDataException("Address must be at least 5 characters", "address")