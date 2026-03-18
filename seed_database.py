import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.models.vendors import Vendors
from app.db.models.stocks import Stocks
from app.db.db_connection import SessionLocal, init_db
from app.repositories.vendor_repository import VendorRepository
from app.repositories.stocks_repository import StockRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

def seed_vendors(session):
    logger.info("Seeding vendors...")
    
    vendor_repo = VendorRepository(session)
    sample_vendors = [
        {
            "name": "Tech Solutions Inc",
            "email": "sales@techsolutions.com",
            "phone": "9876543210",
            "address": "123 Tech Street, Silicon Valley, CA 94025",
            "is_active": True
        },
        {
            "name": "Global Electronics Trading",
            "email": "contact@globalelectronics.com",
            "phone": "9123456789",
            "address": "456 Market Road, New York, NY 10001",
            "is_active": True
        },
        {
            "name": "Precision Hardware Ltd",
            "email": "info@precisionhw.com",
            "phone": "8765432109",
            "address": "789 Industrial Avenue, Austin, TX 78704",
            "is_active": True
        },
    ]
    
    created_vendors = []
    for vendor_data in sample_vendors:
        try:
            vendor = vendor_repo.create(Vendors(**vendor_data))
            created_vendors.append({
                "id": vendor.id,
                "name": vendor.name,
                "email": vendor.email
            })
        except Exception as e:
            print(f"Failed to create vendor {vendor_data['name']}: {str(e)}")
            logger.error(f"Error creating vendor: {str(e)}")
    
    return created_vendors


def seed_stocks(session):
    stock_repo = StockRepository(session)
    sample_stocks = [
        {
            "name": "Dell XPS 13 Laptop",
            "sku": "DELL-XPS-13-2024",
            "description": "High-performance ultrabook with Intel Core i7, 16GB RAM, 512GB SSD",
            "quantity": 45,
            "is_active": True,
            "unit_price": 1299.99
        },
        {
            "name": "Logitech MX Master 3S Mouse",
            "sku": "LOGI-MX-M3S-BLK",
            "description": "Advanced wireless mouse with precision scrolling and customizable buttons",
            "quantity": 150,
            "is_active": True,
            "unit_price": 99.99
        },
        {
            "name": "HP LaserJet Pro M404n Printer",
            "sku": "HP-LJ-PRO-M404N",
            "description": "Network laser printer, 40 ppm, 256MB memory, automatic duplex printing",
            "quantity": 28,
            "is_active": True,
            "unit_price": 449.99
        },
        {
            "name": "Mechanical Keyboard RGB",
            "sku": "MECH-KB-RGB-BLU",
            "description": "Blue switch mechanical keyboard, RGB backlighting, USB-C connection",
            "quantity": 85,
            "is_active": True,
            "unit_price": 149.99
        },
        {
            "name": "27-inch 4K Monitor",
            "sku": "MONITOR-27-4K-IPS",
            "description": "IPS panel, 3840x2160 resolution, USB-C with 90W power delivery",
            "quantity": 32,
            "is_active": True,
            "unit_price": 699.99
        },
        {
            "name": "USB-C Docking Station",
            "sku": "DOCK-USB-C-13PORT",
            "description": "13-port docking station with HDMI, Ethernet, audio, and SD card reader",
            "quantity": 60,
            "is_active": True,
            "unit_price": 189.99
        },
        {
            "name": "Wireless Headphones Pro",
            "sku": "AUDIO-WIRELESS-BLU",
            "description": "Active noise cancellation, 30-hour battery, Bluetooth 5.0",
            "quantity": 120,
            "is_active": True,
            "unit_price": 299.99
        },
        {
            "name": "External SSD 2TB",
            "sku": "SSD-EXT-2TB-NVMe",
            "description": "Portable NVMe SSD, 1050MB/s read speed, USB 3.2 Type-C",
            "quantity": 75,
            "is_active": True,
            "unit_price": 229.99
        },
        {
            "name": "Laptop Stand Adjustable",
            "sku": "STAND-LAPTOP-ALU",
            "description": "Aluminum alloy stand, adjustable height and angle, fits up to 17-inch laptops",
            "quantity": 200,
            "is_active": True,
            "unit_price": 49.99
        },
        {
            "name": "Webcam 4K Professional",
            "sku": "CAM-4K-USB-AUTO",
            "description": "4K UHD, auto-focus, noise-cancelling microphone, USB plug-and-play",
            "quantity": 55,
            "is_active": True,
            "unit_price": 199.99
        },
    ]
    
    created_stocks = []
    for stock_data in sample_stocks:
        try:
            stock = stock_repo.create(Stocks(**stock_data))
            created_stocks.append({
                "id": stock.id,
                "name": stock.name,
                "sku": stock.sku,
                "quantity": stock.quantity
            })
            logger.info(f"Created stock: {stock.name}")
        except Exception as e:
            print(f"Failed to create stock {stock_data['name']}: {str(e)}")
            logger.error(f"Error creating stock: {str(e)}")
    
    return created_stocks


def associate_vendors_with_stocks(session, vendors, stocks):
    stock_repo = StockRepository(session)
    vendor_stock_associations = [
        {"vendor_name": "Tech Solutions Inc", "stock_names": [
            "Dell XPS 13 Laptop",
            "27-inch 4K Monitor",
            "Mechanical Keyboard RGB",
            "Wireless Headphones Pro"
        ]},
        {"vendor_name": "Global Electronics Trading", "stock_names": [
            "Logitech MX Master 3S Mouse",
            "HP LaserJet Pro M404n Printer",
            "USB-C Docking Station",
            "External SSD 2TB"
        ]},
        {"vendor_name": "Precision Hardware Ltd", "stock_names": [
            "27-inch 4K Monitor",
            "Laptop Stand Adjustable",
            "Webcam 4K Professional",
            "Mechanical Keyboard RGB"
        ]},
    ]
    
    for association in vendor_stock_associations:
        vendor_name = association["vendor_name"]
        vendor = next((v for v in vendors if v["name"] == vendor_name), None)
        
        if not vendor:
            print(f"Vendor not found: {vendor_name}")
            continue
        
        for stock_name in association["stock_names"]:
            stock = next((s for s in stocks if s["name"] == stock_name), None)
            
            if not stock:
                print(f"Stock not found: {stock_name}")
                continue
            
            try:
                stock_repo.add_vendor(stock["id"], vendor["id"])
                logger.info(f"Associated vendor {vendor['id']} with stock {stock['id']}")
            except Exception as e:
                print(f"Association failed: {vendor_name} → {stock_name}: {str(e)}")
                logger.warning(f"Error associating vendor with stock: {str(e)}")


def main():
    print("DATABASE SEED SCRIPT - Adding Sample Data")
    
    session = SessionLocal()
    
    try:
        init_db()
        print("Database initialized successfully")
        logger.info("Database initialized")
        
        # Seed vendors
        vendors = seed_vendors(session)
        if not vendors:
            print("No vendors created. Aborting.")
            return False
        
        # Seed stocks
        stocks = seed_stocks(session)
        if not stocks:
            print("No stocks created. Aborting.")
            return False
        
        # Associate vendors with stocks
        associate_vendors_with_stocks(session, vendors, stocks)
        
        print(f"Created {len(vendors)} vendors")
        print(f"Created {len(stocks)} stocks") 
        return True
        
    except Exception as e:
        print(f"Fatal error during seeding: {str(e)}")
        logger.error(f"Fatal error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = main()
    if success:
        print("SUCCESS - Database seeded with sample data")
    else:
        print("FAILED - Check logs for errors")
    
    sys.exit(0 if success else 1)
