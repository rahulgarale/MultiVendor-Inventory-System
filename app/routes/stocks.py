from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from sqlalchemy.orm import Session

from app.schemas.stocks import StockCreate, StockResponse, StockUpdate, StockDetailResponse
from app.db.db_connection import get_db
from app.services.stocks_service import StockService
from app.repositories.stocks_repository import StockRepository
from app.core.exceptions import (
    StockNotFoundException,
    StockAlreadyExistsException,
    InsufficientStockException,
    InvalidVendorDataException,
    DatabaseException,
    IntegrityException
)
from app.core.logging import get_logger

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)

logger = get_logger(__name__)


def get_stock_service(db: Session = Depends(get_db)) -> StockService:
    """
    Dependency provider for StockService.
    """
    repository = StockRepository(db)
    return StockService(repository)


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(
    stock: StockCreate,
    service: StockService = Depends(get_stock_service)
):
    """
    Create a new stock item.
    
    Request body:
    - **name**: Stock item name (unique, 2-255 characters)
    - **sku**: Stock keeping unit (unique, 1-100 characters)
    - **description**: Optional item description
    - **quantity**: Current quantity in stock (≥0)
    - **unit_price**: Price per unit (>0)
    """
    try:
        return service.create(stock)
    
    except StockAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    except InvalidVendorDataException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create stock")
    
    except Exception as e:
        logger.error(f"Unexpected error creating stock: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")



@router.get("/{stock_id}", response_model=StockDetailResponse)
def get_stock(
    stock_id: int,
    service: StockService = Depends(get_stock_service)
):
    """
    Get a specific stock by ID.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    """
    try:
        stock = service.get_by_id(stock_id)
        
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock with ID {stock_id} not found")
        
        return stock
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error fetching stock {stock_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("", response_model=List[StockResponse])
def get_all_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: StockService = Depends(get_stock_service)
):
    """
    Get all stocks with pagination.
    
    Query parameters:
    - **skip**: Number of stocks to skip (default: 0, minimum: 0)
    - **limit**: Maximum number of stocks to return (default: 100, range: 1-1000)
    """
    try:
        return service.get_all(skip=skip, limit=limit)
    
    except Exception as e:
        logger.error(f"Unexpected error fetching stocks: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")



@router.put("/{stock_id}", response_model=StockResponse)
def update_stock(
    stock_id: int,
    stock_update: StockUpdate,
    service: StockService = Depends(get_stock_service)
):
    """
    Update stock information.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    
    Request body (all fields optional):
    - **name**: Stock item name
    - **description**: Item description
    - **quantity**: Current quantity in stock
    - **unit_price**: Price per unit
    """
    try:
        return service.update(stock_id, stock_update)
    
    except StockNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except StockAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    except InvalidVendorDataException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update stock")
    
    except Exception as e:
        logger.error(f"Unexpected error updating stock {stock_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.post("/{stock_id}/adjust-quantity", response_model=StockResponse)
def adjust_stock_quantity(
    stock_id: int,
    quantity_change: int,
    service: StockService = Depends(get_stock_service)
):
    """
    Adjust stock quantity by delta.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    
    Query parameters:
    - **quantity_change**: Change in quantity (positive or negative)
    
    Examples:
    - POST /stocks/1/adjust-quantity?quantity_change=10  # Add 10 items
    - POST /stocks/1/adjust-quantity?quantity_change=-5  # Remove 5 items
    """
    try:
        return service.adjust_quantity(stock_id, quantity_change)
    
    except StockNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except InsufficientStockException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to adjust stock quantity")
    
    except Exception as e:
        logger.error(f"Unexpected error adjusting stock quantity: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(
    stock_id: int,
    service: StockService = Depends(get_stock_service)
):
    """
    Delete a stock by ID.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    """
    try:
        service.delete(stock_id)
    
    except StockNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete stock")
    
    except Exception as e:
        logger.error(f"Unexpected error deleting stock {stock_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.post("/{stock_id}/vendors/{vendor_id}", status_code=status.HTTP_201_CREATED)
def associate_vendor_with_stock(
    stock_id: int,
    vendor_id: int,
    service: StockService = Depends(get_stock_service)
):
    """
    Associate a vendor with a stock as an approved supplier.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    - **vendor_id**: The vendor's unique identifier
    
    This endpoint links a vendor to a stock, allowing the vendor to be selected 
    when placing purchase orders for this stock item.
    """
    try:
        service.add_vendor(stock_id, vendor_id)
        return {"message": f"Vendor {vendor_id} successfully associated with stock {stock_id}"}
    
    except StockNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except InvalidVendorDataException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to associate vendor with stock")
    
    except Exception as e:
        logger.error(f"Unexpected error associating vendor: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("/{stock_id}/vendors", response_model=List[dict])
def get_stock_vendors(
    stock_id: int,
    service: StockService = Depends(get_stock_service)
):
    """
    Get all vendors approved to supply a specific stock.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    
    This endpoint returns a list of vendors that have been linked to this stock item.
    Use this to populate the vendor selection dropdown when creating purchase orders.
    
    Returns:
    - List of vendors with id, name, email, and phone
    """
    try:
        vendors = service.get_vendors(stock_id)
        
        # Convert vendor objects to dict for JSON response
        vendor_list = [
            {
                "id": vendor.id,
                "name": vendor.name,
                "email": vendor.email,
                "phone": vendor.phone,
                "address": vendor.address
            }
            for vendor in vendors
        ]
        
        return vendor_list
    
    except StockNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vendors")
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving vendors: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.delete("/{stock_id}/vendors/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_vendor_from_stock(
    stock_id: int,
    vendor_id: int,
    service: StockService = Depends(get_stock_service)
):
    """
    Disassociate a vendor from a stock.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    - **vendor_id**: The vendor's unique identifier
    
    This endpoint removes a vendor from the list of approved suppliers for a stock item.
    Existing purchase orders with this vendor for this stock are not affected.
    """
    try:
        service.remove_vendor(stock_id, vendor_id)
    
    except StockNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except InvalidVendorDataException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove vendor from stock")
    
    except Exception as e:
        logger.error(f"Unexpected error removing vendor: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")
