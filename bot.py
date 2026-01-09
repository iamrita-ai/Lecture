import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="SerenaBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"),
            sleep_threshold=60,
            workers=20,
            no_updates=False,
            max_concurrent_transmissions=5,
            workdir="."
        )
        self.db = None
        
    async def start(self):
        await super().start()
        
        from database.database import Database
        self.db = Database(Config.MONGO_URI)
        
        me = await self.get_me()
        self.username = me.username
        logger.info(f"✅ {me.first_name} Started!")
        
        try:
            await self.send_message(
                Config.LOG_CHANNEL,
                f"🤖 **{Config.BOT_NAME} Started!**\n\n"
                f"👤 Bot: @{self.username}\n"
                f"🆔 ID: `{me.id}`\n"
                f"📊 Status: Online"
            )
        except Exception as e:
            logger.error(f"Log error: {e}")
    
    async def stop(self, *args):
        await super().stop()
        logger.info("🛑 Bot Stopped!")

bot = Bot()

def start_bot():
    bot.run()

if __name__ == "__main__":
    start_bot()
