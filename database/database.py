from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client['serena_bot']
        self.users = self.db['users']
        self.settings = self.db['settings']
        self.stats = self.db['stats']
        
    async def add_user(self, user_id, username=None):
        """Add new user to database"""
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            await self.users.insert_one({
                "user_id": user_id,
                "username": username,
                "is_premium": False,
                "downloads_today": 0,
                "total_downloads": 0,
                "joined_date": datetime.now(),
                "last_used": datetime.now()
            })
            logger.info(f"New user added: {user_id}")
        else:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_used": datetime.now()}}
            )
    
    async def is_premium(self, user_id):
        """Check if user is premium"""
        user = await self.users.find_one({"user_id": user_id})
        return user.get("is_premium", False) if user else False
    
    async def add_premium(self, user_id):
        """Add premium to user"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": True}},
            upsert=True
        )
    
    async def remove_premium(self, user_id):
        """Remove premium from user"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": False}}
        )
    
    async def get_downloads_today(self, user_id):
        """Get user's downloads today"""
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return 0
        
        # Reset if new day
        last_reset = user.get("last_reset", datetime.now() - timedelta(days=1))
        if datetime.now().date() > last_reset.date():
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"downloads_today": 0, "last_reset": datetime.now()}}
            )
            return 0
        
        return user.get("downloads_today", 0)
    
    async def increment_downloads(self, user_id):
        """Increment user's download count"""
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"downloads_today": 1, "total_downloads": 1},
                "$set": {"last_reset": datetime.now()}
            }
        )
    
    async def get_user_settings(self, user_id):
        """Get user settings"""
        settings = await self.settings.find_one({"user_id": user_id})
        if not settings:
            default = {
                "user_id": user_id,
                "channel_id": None,
                "credit": "Serena",
                "thumbnail_mode": "random"
            }
            await self.settings.insert_one(default)
            return default
        return settings
    
    async def update_settings(self, user_id, key, value):
        """Update user settings"""
        await self.settings.update_one(
            {"user_id": user_id},
            {"$set": {key: value}},
            upsert=True
        )
    
    async def reset_settings(self, user_id):
        """Reset user settings"""
        await self.settings.update_one(
            {"user_id": user_id},
            {"$set": {
                "channel_id": None,
                "credit": "Serena",
                "thumbnail_mode": "random"
            }},
            upsert=True
        )
    
    async def get_bot_stats(self):
        """Get bot statistics"""
        total_users = await self.users.count_documents({})
        premium_users = await self.users.count_documents({"is_premium": True})
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        active_today = await self.users.count_documents({"last_used": {"$gte": today}})
        
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "active_today": active_today
        }
    
    async def is_bot_locked(self):
        """Check if bot is locked"""
        status = await self.stats.find_one({"key": "bot_status"})
        return status.get("locked", False) if status else False
    
    async def lock_bot(self):
        """Lock the bot"""
        await self.stats.update_one(
            {"key": "bot_status"},
            {"$set": {"locked": True}},
            upsert=True
        )
    
    async def unlock_bot(self):
        """Unlock the bot"""
        await self.stats.update_one(
            {"key": "bot_status"},
            {"$set": {"locked": False}},
            upsert=True
  )
