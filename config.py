import os
from os import environ

class Config:
    # Bot Settings
    API_ID = int(environ.get("API_ID", "0"))
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "")
    
    # Database
    MONGO_URI = environ.get("MONGO_URI", "")
    
    # Media
    START_PIC = environ.get("START_PIC", "https://telegra.ph/file/your-image.jpg")
    
    # Hardcoded Values
    LOG_CHANNEL = -1003508789207
    FORCE_SUB = -1003392099253
    OWNERS = [6518065496, 1598576202]
    
    # Bot Settings
    BOT_NAME = "Serena Lec"
    FREE_LIMIT = 10
    DOWNLOAD_DELAY = 5
    PROGRESS_UPDATE_DELAY = 5
    
    # Flask
    PORT = int(environ.get("PORT", 8080))
    
    # Download Settings - Optimized for Render
    CHUNK_SIZE = 2 * 1024 * 1024  # 2MB chunks
    MAX_CONCURRENT_DOWNLOADS = 3
    DOWNLOAD_TIMEOUT = 10800  # 3 hours
    
    # Upload Settings
    UPLOAD_TIMEOUT = 7200  # 2 hours
    
    # Flood Control
    FLOOD_SLEEP = 3
    ETA_UPDATE_INTERVAL = 5
