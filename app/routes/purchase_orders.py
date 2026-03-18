from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from app.schemas.Purchase_order import PurchaseOrderCreate, PurchaseOrderResponse, PurchaseOrderUpdate, PurchaseOrderDetailResponse
from app.db.db_connection import get_db
from app.services.purchase_orders_service import PurchaseOrderService
from app.repositories.purchase_orders_repository import PurchaseOrderRepository
from app.repositories.stocks_repository import StockRepository
from app.repositories.vendor_repository import VendorRepository
from app.core.exceptions import (
    PurchaseOrderNotFoundException,
    InvalidPurchaseOrderStatusException,
    PurchaseOrderOperationException,
    InvalidVendorDataException,
    DatabaseException,
    IntegrityException
)
from app.core.logging import get_logger

router = APIRouter(
    prefix="/purchase-orders",
    tags=["purchase-orders"]
)

logger = get_logger(__name__)


def get_purchase_order_service(db: Session = Depends(get_db)) -> PurchaseOrderService:
    """
    Dependency provider for PurchaseOrderService.
    """
    order_repository = PurchaseOrderRepository(db)
    stock_repository = StockRepository(db)
    vendor_repository = VendorRepository(db)
    return PurchaseOrderService(order_repository, stock_repository, vendor_repository)


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    order: PurchaseOrderCreate,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Create a new purchase order.
    
    Request body:
    - **stock_id**: ID of the stock item to order (must exist)
    - **vendor_id**: ID of the vendor supplying the stock (must exist)
    - **quantity**: Order quantity (>0)
    - **notes**: Optional order notes
    """
    try:
        return service.create(order)
    
    except PurchaseOrderOperationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    
    except InvalidVendorDataException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create purchase order")
    
    except Exception as e:
        logger.error(f"Unexpected error creating purchase order: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("/{order_id}", response_model=PurchaseOrderDetailResponse)
def get_purchase_order(
    order_id: int,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Get a specific purchase order by ID.
    
    Path parameters:
    - **order_id**: The purchase order's unique identifier
    """
    try:
        order = service.get_by_id(order_id)
        
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase order with ID {order_id} not found")
        
        return order
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error fetching purchase order {order_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("", response_model=List[PurchaseOrderResponse])
def get_all_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Get all purchase orders with pagination.
    
    Query parameters:
    - **skip**: Number of orders to skip (default: 0, minimum: 0)
    - **limit**: Maximum number of orders to return (default: 100, range: 1-1000)
    """
    try:
        return service.get_all(skip=skip, limit=limit)
    
    except Exception as e:
        logger.error(f"Unexpected error fetching purchase orders: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("/by-status/{order_status}", response_model=List[PurchaseOrderResponse])
def get_orders_by_status(
    order_status: str,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Get purchase orders by status.
    
    Path parameters:
    - **order_status**: Order status (pending, confirmed, delivered, cancelled)
    """
    try:
        return service.get_by_status(order_status)
    
    except PurchaseOrderOperationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except Exception as e:
        logger.error(f"Unexpected error fetching orders by status: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("/vendor/{vendor_id}", response_model=List[PurchaseOrderResponse])
def get_orders_by_vendor(
    vendor_id: int,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Get all purchase orders for a specific vendor.
    
    Path parameters:
    - **vendor_id**: The vendor's unique identifier
    """
    try:
        return service.get_by_vendor(vendor_id)
    
    except Exception as e:
        logger.error(f"Unexpected error fetching orders by vendor: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.get("/stock/{stock_id}", response_model=List[PurchaseOrderResponse])
def get_orders_by_stock(
    stock_id: int,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Get all purchase orders for a specific stock.
    
    Path parameters:
    - **stock_id**: The stock's unique identifier
    """
    try:
        return service.get_by_stock(stock_id)
    
    except Exception as e:
        logger.error(f"Unexpected error fetching orders by stock: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    order_id: int,
    order_update: PurchaseOrderUpdate,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Update purchase order information.
    
    Path parameters:
    - **order_id**: The purchase order's unique identifier
    
    Request body (all fields optional):

    - **notes**: Updated order notes
    """
    try:
        return service.update(order_id, order_update)
    
    except PurchaseOrderNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except InvalidPurchaseOrderStatusException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    except InvalidVendorDataException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update purchase order")
    
    except Exception as e:
        logger.error(f"Unexpected error updating purchase order {order_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.post("/{order_id}/status/{new_status}", response_model=PurchaseOrderResponse)
def update_order_status(
    order_id: int,
    new_status: str,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Update purchase order status with validation.
    
    Path parameters:
    - **order_id**: The purchase order's unique identifier
    - **new_status**: New status (pending, confirmed, delivered, cancelled)
    
    Valid transitions:
    - pending → confirmed, cancelled
    - confirmed → delivered, cancelled
    - delivered → (final state)
    - cancelled → (final state)
    """
    try:
        return service.update_status(order_id, new_status)
    
    except PurchaseOrderNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except InvalidPurchaseOrderStatusException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    except PurchaseOrderOperationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order status")
    
    except Exception as e:
        logger.error(f"Unexpected error updating order status: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(
    order_id: int,
    service: PurchaseOrderService = Depends(get_purchase_order_service)
):
    """
    Delete a purchase order by ID.
    
    IMPORTANT: Only pending orders can be deleted.
    - Confirmed orders must be cancelled via status transition
    - Delivered/Cancelled orders cannot be deleted (audit trail)
    
    Path parameters:
    - **order_id**: The purchase order's unique identifier
    """
    try:
        service.delete(order_id)
    
    except PurchaseOrderNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    
    except PurchaseOrderOperationException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    
    except (DatabaseException, IntegrityException) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete purchase order")
    
    except Exception as e:
        logger.error(f"Unexpected error deleting purchase order {order_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")
