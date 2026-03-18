from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from sqlalchemy.orm import Session

from app.schemas.vendors import VendorCreate, VendorResponse, VendorUpdate
from app.db.db_connection import get_db
from app.services.vendor_service import VendorService
from app.repositories.vendor_repository import VendorRepository
from app.core.exceptions import (
    VendorNotFoundException,
    VendorAlreadyExistsException,
    InvalidVendorDataException,
    EmailValidationException,
    PhoneValidationException,
    DatabaseException,
    IntegrityException
)
from app.core.logging import get_logger

router = APIRouter(
    prefix="/vendors",
    tags=["vendors"]
)

logger = get_logger(__name__)


def get_vendor_service(db: Session = Depends(get_db)) -> VendorService:
    """
    Dependency provider for VendorService.
    """
    repository = VendorRepository(db)
    return VendorService(repository)


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor: VendorCreate,
    service: VendorService = Depends(get_vendor_service)
):
    """
    Create a new vendor.
    
    Request body:
    - **name**: Vendor name (unique, 2-255 characters)
    - **email**: Vendor email address (valid email format)
    - **phone**: Contact phone number (valid phone format)
    - **address**: Vendor address (minimum 5 characters)
    
    Returns:
        201 CREATED: Newly created vendor with ID
        400 BAD REQUEST: Validation failed or vendor already exists
        500 INTERNAL SERVER ERROR: Database error
    """
    try:
        return service.create(vendor)
    
    except VendorAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    
    except (InvalidVendorDataException, EmailValidationException, PhoneValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vendor"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error creating vendor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )

@router.get("/active", response_model=List[VendorResponse])
def get_active_vendors(
    service: VendorService = Depends(get_vendor_service)
):
    """
    Get all active vendors only.
    
    Returns:
        200 OK: List of active vendors
        500 INTERNAL SERVER ERROR: Database error
    """
    try:
        return service.get_active()
    
    except Exception as e:
        logger.error(f"Unexpected error fetching active vendors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )



@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    service: VendorService = Depends(get_vendor_service)
):
    """
    Get a specific vendor by ID.
    
    Path parameters:
    - **vendor_id**: The vendor's unique identifier
    
    Returns:
        200 OK: Vendor details
        404 NOT FOUND: Vendor not found
    """
    try:
        vendor = service.get_by_id(vendor_id)
        
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID {vendor_id} not found"
            )
        
        return vendor
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error fetching vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )


@router.get("", response_model=List[VendorResponse])
def get_all_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: VendorService = Depends(get_vendor_service)
):
    """
    Get all vendors with pagination.
    
    Query parameters:
    - **skip**: Number of vendors to skip (default: 0, minimum: 0)
    - **limit**: Maximum number of vendors to return (default: 100, range: 1-1000)
    
    Returns:
        200 OK: List of vendors
        500 INTERNAL SERVER ERROR: Database error
    """
    try:
        return service.get_all(skip=skip, limit=limit)
    
    except Exception as e:
        logger.error(f"Unexpected error fetching vendors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    vendor_update: VendorUpdate,
    service: VendorService = Depends(get_vendor_service)
):
    """
    Update vendor information.
    
    Path parameters:
    - **vendor_id**: The vendor's unique identifier
    
    Request body (all fields optional):
    - **name**: Vendor name
    - **email**: Vendor email address
    - **phone**: Contact phone number
    - **address**: Vendor address
    - **is_active**: Active status (true/false)
    
    Returns:
        200 OK: Updated vendor details
        404 NOT FOUND: Vendor not found
        409 CONFLICT: Name or email already in use
        422 UNPROCESSABLE ENTITY: Validation failed
        500 INTERNAL SERVER ERROR: Database error
    """
    try:
        return service.update(vendor_id, vendor_update)
    
    except VendorNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except VendorAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    
    except (InvalidVendorDataException, EmailValidationException, PhoneValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vendor"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error updating vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: int,
    service: VendorService = Depends(get_vendor_service)
):
    """
    Delete a vendor by ID.
    
    Path parameters:
    - **vendor_id**: The vendor's unique identifier
    
    Returns:
        204 NO CONTENT: Vendor successfully deleted
        404 NOT FOUND: Vendor not found
        500 INTERNAL SERVER ERROR: Database error
    """
    try:
        service.delete(vendor_id)
    
    except VendorNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vendor"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error deleting vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred"
        )