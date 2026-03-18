
class ApplicationException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# Vendor Exceptions
class VendorException(ApplicationException):
    """Base exception for vendor-related errors."""
    pass


class VendorNotFoundException(VendorException):
    """Raised when a vendor is not found."""
    
    def __init__(self, vendor_id: int):
        super().__init__(
            message=f"Vendor with ID {vendor_id} not found",
            code="VENDOR_NOT_FOUND"
        )
        self.vendor_id = vendor_id


class VendorAlreadyExistsException(VendorException):
    """Raised when trying to create a vendor with duplicate unique field."""
    
    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"Vendor with {field} '{value}' already exists",
            code="VENDOR_ALREADY_EXISTS"
        )
        self.field = field
        self.value = value


class InvalidVendorDataException(VendorException):
    """Raised when vendor data is invalid."""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            code="INVALID_VENDOR_DATA"
        )
        self.field = field


# Stock Exceptions
class StockException(ApplicationException):
    """Base exception for stock-related errors."""
    pass


class StockNotFoundException(StockException):
    """Raised when a stock item is not found."""
    
    def __init__(self, stock_id: int):
        super().__init__(
            message=f"Stock with ID {stock_id} not found",
            code="STOCK_NOT_FOUND"
        )
        self.stock_id = stock_id


class InsufficientStockException(StockException):
    """Raised when stock quantity is insufficient."""
    
    def __init__(self, stock_id: int, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock. Requested: {requested}, Available: {available}",
            code="INSUFFICIENT_STOCK"
        )
        self.stock_id = stock_id
        self.requested = requested
        self.available = available


class StockAlreadyExistsException(StockException):
    """Raised when trying to create a stock with duplicate SKU."""
    
    def __init__(self, sku: str):
        super().__init__(
            message=f"Stock with SKU '{sku}' already exists",
            code="STOCK_ALREADY_EXISTS"
        )
        self.sku = sku


# Purchase Order Exceptions
class PurchaseOrderException(ApplicationException):
    """Base exception for purchase order-related errors."""
    pass


class PurchaseOrderNotFoundException(PurchaseOrderException):
    """Raised when a purchase order is not found."""
    
    def __init__(self, order_id: int):
        super().__init__(
            message=f"Purchase order with ID {order_id} not found",
            code="PURCHASE_ORDER_NOT_FOUND"
        )
        self.order_id = order_id


class InvalidPurchaseOrderStatusException(PurchaseOrderException):
    """Raised when attempting invalid status transition."""
    
    def __init__(self, current_status: str, requested_status: str):
        super().__init__(
            message=f"Cannot transition from '{current_status}' to '{requested_status}'",
            code="INVALID_ORDER_STATUS"
        )
        self.current_status = current_status
        self.requested_status = requested_status


class PurchaseOrderOperationException(PurchaseOrderException):
    """Raised when an operation on purchase order fails."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="PURCHASE_ORDER_OPERATION_ERROR"
        )


# Database Exceptions
class DatabaseException(ApplicationException):
    """Base exception for database-related errors."""
    pass


class TransactionException(DatabaseException):
    """Raised when a database transaction fails."""
    
    def __init__(self, message: str = "Database transaction failed"):
        super().__init__(
            message=message,
            code="TRANSACTION_ERROR"
        )


class IntegrityException(DatabaseException):
    """Raised when database integrity constraint is violated."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="INTEGRITY_ERROR"
        )


# Validation Exceptions
class ValidationException(ApplicationException):
    """Base exception for validation errors."""
    pass


class EmailValidationException(ValidationException):
    """Raised when email format is invalid."""
    
    def __init__(self, email: str):
        super().__init__(
            message=f"Invalid email format: {email}",
            code="INVALID_EMAIL"
        )
        self.email = email


class PhoneValidationException(ValidationException):
    """Raised when phone format is invalid."""
    
    def __init__(self, phone: str):
        super().__init__(
            message=f"Invalid phone format: {phone}",
            code="INVALID_PHONE"
        )
        self.phone = phone
