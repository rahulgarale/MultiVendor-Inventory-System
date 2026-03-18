from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from app.db.db_connection import init_db, settings
from app.core.logging import setup_logging, get_logger
from app.routes import vendors, stocks, purchase_orders  # Import routers

# Initialize logging
logger = setup_logging(log_level="INFO" if not settings.debug_mode else "DEBUG")
app_logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Starting up the application...")
    init_db() 
    app_logger.info("Database initialized successfully.")
    yield  # Run the application
    app_logger.info("Application shutdown complete.")

app = FastAPI(
    title=settings.app_name,
    description="Backend system for managing inventory across multiple vendors in a restaurant.",
    version=settings.app_version,
    debug=settings.debug_mode,
    lifespan=lifespan,
)

# Include routers
app.include_router(vendors.router, prefix=settings.api_prefix)
app.include_router(stocks.router, prefix=settings.api_prefix)
app.include_router(purchase_orders.router, prefix=settings.api_prefix)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is healthy and running."}

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the Inventory Management API.",
        "version": settings.app_version,
        "documentation": f"{settings.api_prefix}/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )