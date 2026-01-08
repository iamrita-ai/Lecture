from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import WebpageMediaEmpty, MediaEmpty
from config import Config
import time

START_TEXT = """
👋 **Welcome to {}!**

🎓 **Your Ultimate Study Companion**

Download lectures, PDFs, and study materials from 25+ Indian coaching platforms.

✨ **Features:**
• 📚 Download from coaching apps
• 🔐 Secure login with OTP
• 📦 Batch downloads via TXT
• 🎯 Single file downloads
• 🛑 Cancel anytime with /cancel

👇 **Get Started!**
"""

HELP_TEXT = """
📖 **{} - Quick Guide**

**Commands:**
• /start - Start bot
• /help - This message
• /login - Login to platform
• /setting - Configure
• /cancel - Stop task
• /ping - Check speed

**Usage:**

**1️⃣ Login & Batch Download** (Premium)
• /login → Select app
• Enter phone & OTP (572002)
• Select batch → Get TXT
• Send TXT back → Download all

**2️⃣ Single File** (Free/Premium)
• Send direct video/PDF link
• Bot downloads & sends

**3️⃣ Custom TXT**
Format: `Title | URL` (each line)

**Free:** 10 files/day
**Premium:** Unlimited

**Supported Platforms:**
PW, Unacademy, Vedantu, BYJU'S, Khan Academy, RG Vikramjeet, Carrier Will, Study IQ, Exampur, Utkarsh, Rojgar with Ankit, Vidyakul, Aakash, Target with Ankit, EduRev, SSC Maker, SmartKida & more!

Need help? Contact owner!
"""

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    await client.db.add_user(user_id, message.from_user.username)
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        await message.reply_text(
            "🔒 **Bot is Currently Locked!**\n\n"
            "Contact owner to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
            ])
        )
        return
    
    # Check force subscription
    try:
        member = await client.get_chat_member(Config.FORCE_SUB, user_id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(
                "⚠️ **Join Our Channel First!**\n\n"
                "Please join our channel to use this bot.\n"
                "After joining, click /start again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url="https://t.me/serenaunzipbot")],
                    [InlineKeyboardButton("🔄 Refresh", callback_data="check_subscription")]
                ])
            )
            return
    except Exception as e:
        print(f"Force sub error: {e}")
    
    # Create buttons with Force Sub and Owner
    buttons = [
        [InlineKeyboardButton("📚 Login to App", callback_data="login_menu")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
    ]
    
    try:
        if Config.START_PIC and Config.START_PIC.startswith('http'):
            await message.reply_photo(
                photo=Config.START_PIC,
                caption=START_TEXT.format(Config.BOT_NAME),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await message.reply_text(
                START_TEXT.format(Config.BOT_NAME),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except (WebpageMediaEmpty, MediaEmpty, Exception):
        await message.reply_text(
            START_TEXT.format(Config.BOT_NAME),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    try:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"#NEW_USER\n\n"
            f"👤 {message.from_user.mention}\n"
            f"🆔 `{user_id}`\n"
            f"👥 @{message.from_user.username or 'None'}\n"
            f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        print(f"Log error: {e}")

@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription_callback(client: Client, query):
    """Check if user joined channel"""
    user_id = query.from_user.id
    
    try:
        member = await client.get_chat_member(Config.FORCE_SUB, user_id)
        if member.status not in ["left", "kicked"]:
            # User joined, show start message
            buttons = [
                [InlineKeyboardButton("📚 Login to App", callback_data="login_menu")],
                [InlineKeyboardButton("❓ Help", callback_data="help"),
                 InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
                [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena"),
                 InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
            ]
            
            await query.message.edit_text(
                START_TEXT.format(Config.BOT_NAME),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await query.answer("✅ Subscription verified!", show_alert=False)
        else:
            await query.answer("⚠️ Please join the channel first!", show_alert=True)
    except Exception as e:
        await query.answer("⚠️ Please join the channel first!", show_alert=True)

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
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
        [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
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
        [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
    ]
    
    try:
        if hasattr(query.message, 'photo') and query.message.photo:
            await query.message.edit_caption(
                caption=START_TEXT.format(Config.BOT_NAME),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await query.message.edit_text(
                text=START_TEXT.format(Config.BOT_NAME),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception:
        try:
            await query.message.delete()
            await query.message.chat.send_message(
                text=START_TEXT.format(Config.BOT_NAME),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except:
            pass

@Client.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    end = time.time()
    await msg.edit_text(f"🏓 **Pong!**\n⚡ `{(end-start)*1000:.2f}ms`")
