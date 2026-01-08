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
    FREE_LIMIT = 10  # Videos per day for free users
    DOWNLOAD_DELAY = 5  # Seconds between downloads
    
    # Flask
    PORT = int(environ.get("PORT", 8080))
