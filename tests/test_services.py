import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.services.vendor_service import VendorService
from app.services.stocks_service import StockService
from app.services.purchase_orders_service import PurchaseOrderService
from app.db.status_enum import OrderStatus
from app.core.exceptions import (
    VendorAlreadyExistsException,
    VendorNotFoundException,
    EmailValidationException,
    PhoneValidationException,
    StockNotFoundException,
    StockAlreadyExistsException,
    InsufficientStockException,
    InvalidVendorDataException,
    PurchaseOrderNotFoundException,
    PurchaseOrderOperationException,
)


# ── Fixtures ──

@pytest.fixture
def mock_vendor_repo():
    return MagicMock()

@pytest.fixture
def mock_stock_repo():
    return MagicMock()

@pytest.fixture
def mock_order_repo():
    return MagicMock()

@pytest.fixture
def vendor_service(mock_vendor_repo):
    return VendorService(mock_vendor_repo)

@pytest.fixture
def stock_service(mock_stock_repo):
    return StockService(mock_stock_repo)

@pytest.fixture
def order_service(mock_order_repo, mock_stock_repo, mock_vendor_repo):
    return PurchaseOrderService(mock_order_repo, mock_stock_repo, mock_vendor_repo)


def _make_vendor_create(**overrides):
    data = {"name": "Test Vendor", "email": "test@vendor.com", "phone": "9876543210", "address": "123 Test Street, City"}
    data.update(overrides)
    from app.schemas.vendors import VendorCreate
    return VendorCreate(**data)


def _make_stock_create(**overrides):
    data = {"name": "Test Item", "sku": "TST-001", "quantity": 100, "unit_price": 49.99}
    data.update(overrides)
    from app.schemas.stocks import StockCreate
    return StockCreate(**data)


def _make_order_create(**overrides):
    data = {"stock_id": 1, "vendor_id": 1, "quantity": 10}
    data.update(overrides)
    from app.schemas.Purchase_order import PurchaseOrderCreate
    return PurchaseOrderCreate(**data)


def _make_mock_order(id=1, stock_id=1, vendor_id=1, quantity=10, status=OrderStatus.PENDING, created_at=None):
    order = MagicMock()
    order.id = id
    order.stock_id = stock_id
    order.vendor_id = vendor_id
    order.quantity = quantity
    order.status = status
    order.created_at = created_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
    return order


def _make_mock_stock(id=1, quantity=100, is_active=True, vendors=None):
    stock = MagicMock()
    stock.id = id
    stock.quantity = quantity
    stock.is_active = is_active
    stock.vendors = vendors or []
    stock.name = "Test Item"
    stock.sku = "TST-001"
    return stock


def _make_mock_vendor(id=1, is_active=True):
    vendor = MagicMock()
    vendor.id = id
    vendor.is_active = is_active
    vendor.name = "Test Vendor"
    vendor.email = "test@vendor.com"
    return vendor


# ── Vendor Service Tests ──

class TestVendorService:

    def test_create_vendor_duplicate_name_raises(self, vendor_service, mock_vendor_repo):
        mock_vendor_repo.get_by_name.return_value = _make_mock_vendor()
        with pytest.raises(VendorAlreadyExistsException):
            vendor_service.create(_make_vendor_create())

    def test_create_vendor_duplicate_email_raises(self, vendor_service, mock_vendor_repo):
        mock_vendor_repo.get_by_name.return_value = None
        mock_vendor_repo.get_by_email.return_value = _make_mock_vendor()
        with pytest.raises(VendorAlreadyExistsException):
            vendor_service.create(_make_vendor_create())

    def test_create_vendor_invalid_email_raises(self, vendor_service):
        with pytest.raises(EmailValidationException):
            vendor_service.create(_make_vendor_create(email="not-an-email"))

    def test_create_vendor_invalid_phone_raises(self, vendor_service):
        with pytest.raises(PhoneValidationException):
            vendor_service.create(_make_vendor_create(phone="abcdefghij"))

    def test_delete_nonexistent_vendor_raises(self, vendor_service, mock_vendor_repo):
        mock_vendor_repo.exists.return_value = False
        with pytest.raises(VendorNotFoundException):
            vendor_service.delete(999)


# ── Stock Service Tests ──

class TestStockService:

    def test_create_stock_duplicate_sku_raises(self, stock_service, mock_stock_repo):
        mock_stock_repo.get_by_sku.return_value = _make_mock_stock()
        with pytest.raises(StockAlreadyExistsException):
            stock_service.create(_make_stock_create())

    def test_adjust_quantity_insufficient_raises(self, stock_service, mock_stock_repo):
        mock_stock_repo.get_by_id.return_value = _make_mock_stock(quantity=5)
        with pytest.raises(InsufficientStockException):
            stock_service.adjust_quantity(1, -10)

    def test_adjust_quantity_success(self, stock_service, mock_stock_repo):
        mock_stock_repo.get_by_id.return_value = _make_mock_stock(quantity=50)
        mock_stock_repo.update_quantity.return_value = _make_mock_stock(quantity=40)
        result = stock_service.adjust_quantity(1, -10)
        mock_stock_repo.update_quantity.assert_called_once_with(1, -10)

    def test_delete_nonexistent_stock_raises(self, stock_service, mock_stock_repo):
        mock_stock_repo.exists.return_value = False
        with pytest.raises(StockNotFoundException):
            stock_service.delete(999)


# ── Purchase Order Service Tests ──

class TestPurchaseOrderService:

    def test_create_order_with_inactive_stock_raises(self, order_service, mock_stock_repo):
        mock_stock_repo.get_by_id.return_value = _make_mock_stock(is_active=False)
        with pytest.raises(PurchaseOrderOperationException, match="not active"):
            order_service.create(_make_order_create())

    def test_create_order_with_unapproved_vendor_raises(self, order_service, mock_stock_repo, mock_vendor_repo):
        approved_vendor = _make_mock_vendor(id=99)
        stock = _make_mock_stock(vendors=[approved_vendor])
        mock_stock_repo.get_by_id.return_value = stock
        mock_vendor_repo.get_by_id.return_value = _make_mock_vendor(id=1)
        with pytest.raises(PurchaseOrderOperationException, match="not an approved supplier"):
            order_service.create(_make_order_create(vendor_id=1))

    def test_create_order_insufficient_stock_raises(self, order_service, mock_stock_repo, mock_vendor_repo):
        vendor = _make_mock_vendor(id=1)
        stock = _make_mock_stock(quantity=5, vendors=[vendor])
        mock_stock_repo.get_by_id.return_value = stock
        mock_vendor_repo.get_by_id.return_value = vendor
        with pytest.raises(PurchaseOrderOperationException, match="Insufficient stock"):
            order_service.create(_make_order_create(quantity=10))

    def test_delete_confirmed_order_raises(self, order_service, mock_order_repo):
        order = _make_mock_order(status=OrderStatus.CONFIRMED)
        mock_order_repo.get_by_id.return_value = order
        with pytest.raises(PurchaseOrderOperationException, match="Cannot delete"):
            order_service.delete(1)

    def test_delete_nonexistent_order_raises(self, order_service, mock_order_repo):
        mock_order_repo.get_by_id.return_value = None
        with pytest.raises(PurchaseOrderNotFoundException):
            order_service.delete(999)

    def test_update_status_invalid_raises(self, order_service, mock_order_repo):
        mock_order_repo.get_by_id.return_value = _make_mock_order()
        with pytest.raises(PurchaseOrderOperationException, match="Invalid status"):
            order_service.update_status(1, "shipped")

    def test_update_status_nonexistent_order_raises(self, order_service, mock_order_repo):
        mock_order_repo.get_by_id.return_value = None
        with pytest.raises(PurchaseOrderNotFoundException):
            order_service.update_status(999, "confirmed")

    def test_confirm_deducts_stock(self, order_service, mock_order_repo, mock_stock_repo):
        order = _make_mock_order(quantity=10, status=OrderStatus.PENDING)
        stock = _make_mock_stock(quantity=50)
        mock_order_repo.get_by_id.return_value = order
        mock_order_repo.get_by_status.return_value = [order]
        mock_stock_repo.get_by_id.return_value = stock
        mock_order_repo.update_status.return_value = order

        order_service.update_status(1, "confirmed")

        mock_stock_repo.update.assert_called_once_with(1, {"quantity": 40})

    def test_cancel_confirmed_restores_stock(self, order_service, mock_order_repo, mock_stock_repo):
        order = _make_mock_order(quantity=10, status=OrderStatus.CONFIRMED)
        stock = _make_mock_stock(quantity=40)
        mock_order_repo.get_by_id.return_value = order
        mock_stock_repo.get_by_id.return_value = stock
        mock_order_repo.update_status.return_value = order

        order_service.update_status(1, "cancelled")

        mock_stock_repo.update.assert_called_once_with(1, {"quantity": 50})

    def test_fifo_blocks_out_of_order_confirmation(self, order_service, mock_order_repo, mock_stock_repo):
        earlier_order = _make_mock_order(id=1, stock_id=1, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        later_order = _make_mock_order(id=2, stock_id=1, created_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
        mock_order_repo.get_by_id.return_value = later_order
        mock_order_repo.get_by_status.return_value = [earlier_order, later_order]
        mock_stock_repo.get_by_id.return_value = _make_mock_stock(quantity=100)

        with pytest.raises(PurchaseOrderOperationException, match="Earlier orders"):
            order_service.update_status(2, "confirmed")

    def test_get_by_invalid_status_raises(self, order_service):
        with pytest.raises(PurchaseOrderOperationException, match="Invalid status"):
            order_service.get_by_status("nonexistent")
