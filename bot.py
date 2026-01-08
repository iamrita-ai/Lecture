import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from config import Config
import logging
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="SerenaBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"),
            sleep_threshold=30
        )
        self.db = Database(Config.MONGO_URI)
        
    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username = me.username
        logger.info(f"✅ {me.first_name} Started!")
        
        # Send start notification to log channel
        try:
            await self.send_message(
                Config.LOG_CHANNEL,
                f"🤖 **{Config.BOT_NAME} Started Successfully!**\n\n"
                f"👤 Bot: @{self.username}\n"
                f"🆔 ID: `{me.id}`\n"
                f"📊 Status: Active"
            )
        except Exception as e:
            logger.error(f"Failed to send start message: {e}")
    
    async def stop(self, *args):
        await super().stop()
        logger.info("🛑 Bot Stopped!")

bot = Bot()

def start_bot():
    bot.run()

if __name__ == "__main__":
    start_bot()
