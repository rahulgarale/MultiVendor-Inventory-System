from pydantic_settings import BaseSettings

class GlobalConfig(BaseSettings):
    app_name: str = "Multi-Vendor Inventory System"
    app_version: str = "0.0.1"
    debug_mode: bool = False
    database_url: str = "postgresql://user:password@localhost:5432/inventory_db"    
    
    api_prefix: str = "/api/v1"


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = GlobalConfig()