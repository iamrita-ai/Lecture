from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import Config
import time

START_TEXT = """
👋 **Welcome to {}!**

🎓 **Your Ultimate Study Companion**

I can help you download lectures, PDFs, and study materials from various online coaching platforms.

✨ **Features:**
• 📚 Download videos & PDFs from coaching apps
• 🔐 Secure login with OTP
• 📦 Batch downloads
• 💾 Auto-delete after sending
• 📊 Download progress tracking
• 🛑 Cancel anytime with /cancel

👇 **Click below to get started!**
"""

HELP_TEXT = """
📖 **How to Use {}**

**Step 1️⃣ - Login**
• Use /login to select your coaching app
• Enter your phone number (with country code optional)
• Enter OTP: `5 7 2 0 0 2`
• Select your purchased batch

**Step 2️⃣ - Generate TXT File**
• Click on batch or send batch ID
• Bot will create a TXT file with all videos/PDFs

**Step 3️⃣ - Download**
• Send the TXT file back to bot
• Bot will download and send all files
• Files auto-delete after sending
• Use /cancel to stop anytime

**📝 Example:**
1. /login → Select "Physics Wallah"
2. Enter: +919876543210
3. Enter OTP: 5 7 2 0 0 2
4. Select batch → Get TXT file
5. Send TXT file → Get all downloads

**⚙️ Commands:**
• /start - Start the bot
• /help - Get this help message
• /login - Login to coaching app
• /setting - Configure settings
• /cancel - Cancel ongoing task
• /ping - Check bot speed

**🆓 Free Users:** 10 videos/day
**💎 Premium:** Unlimited downloads

**✅ Supported Apps:**
• Physics Wallah (PW)
• Unacademy
• Vedantu
• BYJU'S
• Khan Academy India
• Toppr
• Doubtnut
• Embibe
• Gradeup
• Testbook
• Adda247
• Oliveboard
• And many more...

**💡 Tips:**
• Works in groups with topics
• Random thumbnails on 1/3 videos
• All actions logged in log channel
• Use /cancel to stop downloads
"""

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Add user to database
    await client.db.add_user(user_id, message.from_user.username)
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        await message.reply_text(
            "🔒 **Bot is Currently Locked!**\n\n"
            "Please contact the owner to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Owner", url=f"tg://user?id={Config.OWNERS[0]}")]
            ])
        )
        return
    
    # Check force subscription
    try:
        member = await client.get_chat_member(Config.FORCE_SUB, user_id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(
                "⚠️ **You must join our channel first!**\n\n"
                "Please join the channel and click /start again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{(await client.get_chat(Config.FORCE_SUB)).username or 'channel'}")]
                ])
            )
            return
    except Exception as e:
        pass
    
    # Send start message
    buttons = [
        [InlineKeyboardButton("📚 Login to App", callback_data="login_menu")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("👤 Owner", url=f"tg://user?id={Config.OWNERS[0]}"),
         InlineKeyboardButton("📢 Channel", url=f"https://t.me/{(await client.get_chat(Config.FORCE_SUB)).username or 'channel'}")]
    ]
    
    await message.reply_photo(
        photo=Config.START_PIC,
        caption=START_TEXT.format(Config.BOT_NAME),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    # Log to channel
    try:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"#NEW_USER\n\n"
            f"👤 User: {message.from_user.mention}\n"
            f"🆔 ID: `{user_id}`\n"
            f"👥 Username: @{message.from_user.username or 'None'}\n"
            f"📅 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except:
        pass

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("👤 Owner", url=f"tg://user?id={Config.OWNERS[0]}")]
    ]
    
    await message.reply_text(
        HELP_TEXT.format(Config.BOT_NAME),
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Client, query):
    buttons = [
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("👤 Owner", url=f"tg://user?id={Config.OWNERS[0]}")]
    ]
    
    await query.message.edit_text(
        HELP_TEXT.format(Config.BOT_NAME),
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("^start$"))
async def start_callback(client: Client, query):
    buttons = [
        [InlineKeyboardButton("📚 Login to App", callback_data="login_menu")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("👤 Owner", url=f"tg://user?id={Config.OWNERS[0]}"),
         InlineKeyboardButton("📢 Channel", url=f"https://t.me/{(await client.get_chat(Config.FORCE_SUB)).username or 'channel'}")]
    ]
    
    await query.message.edit_caption(
        caption=START_TEXT.format(Config.BOT_NAME),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    end = time.time()
    await msg.edit_text(f"🏓 **Pong!**\n⚡ Response: `{(end-start)*1000:.2f}ms`")
