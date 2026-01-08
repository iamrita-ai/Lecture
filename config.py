import os
from os import environ

class Config:
    # Bot Settings
    API_ID = int(environ.get("API_ID", "0"))
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "")
    
    # Database
    MONGO_URI = environ.get("MONGO_URI", "")
    
    # Media - Valid default Telegraph image
    START_PIC = environ.get("START_PIC", "https://telegra.ph/file/f9e2b5d76b8b6f8f8f8f8.jpg")
    
    # Hardcoded Values
    LOG_CHANNEL = -1003508789207
    FORCE_SUB = -1003392099253
    OWNERS = [6518065496, 1598576202]
    
    # Bot Settings
    BOT_NAME = "Serena Lec"
    FREE_LIMIT = 10  # Videos per day for free users (Optional - Change Kar Sakte Ho)
    DOWNLOAD_DELAY = 5  # Seconds between downloads (Optional - Change Kar Sakte Ho)
    PROGRESS_UPDATE_DELAY = 3  # Seconds between progress updates (Optional)
    
    # Flask
    PORT = int(environ.get("PORT", 8080))
    
    # Download Settings (Optional - Customize Kar Sakte Ho)
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    MAX_CONCURRENT_DOWNLOADS = 3  # Maximum simultaneous downloads
    
    # Flood Control (Optional)
    FLOOD_SLEEP = 5  # Default sleep time between files
    ETA_UPDATE_INTERVAL = 2  # Update ETA every 2 seconds
