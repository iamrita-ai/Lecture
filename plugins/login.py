from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import Config
from utils.session import set_user_state, get_user_state, clear_user_state, update_user_data
import re
import asyncio

# Comprehensive Indian Coaching Apps
COACHING_APPS = {
    "pw": {"name": "📚 Physics Wallah", "icon": "📚"},
    "unacademy": {"name": "🎓 Unacademy", "icon": "🎓"},
    "vedantu": {"name": "📖 Vedantu", "icon": "📖"},
    "byjus": {"name": "🔬 BYJU'S", "icon": "🔬"},
    "khan": {"name": "🌟 Khan Academy", "icon": "🌟"},
    "toppr": {"name": "🎯 Toppr", "icon": "🎯"},
    "doubtnut": {"name": "❓ Doubtnut", "icon": "❓"},
    "embibe": {"name": "📊 Embibe", "icon": "📊"},
    "gradeup": {"name": "📈 Gradeup", "icon": "📈"},
    "testbook": {"name": "📝 Testbook", "icon": "📝"},
    "adda247": {"name": "💯 Adda247", "icon": "💯"},
    "oliveboard": {"name": "🎪 Oliveboard", "icon": "🎪"},
    "rgvikramjeet": {"name": "🎖️ RG Vikramjeet", "icon": "🎖️"},
    "carrierwill": {"name": "🚀 Carrier Will", "icon": "🚀"},
    "studyiq": {"name": "🧠 Study IQ", "icon": "🧠"},
    "exampur": {"name": "📘 Exampur", "icon": "📘"},
    "utkarsh": {"name": "⭐ Utkarsh", "icon": "⭐"},
    "rojgarwithankit": {"name": "💼 Rojgar with Ankit", "icon": "💼"},
    "vidyakul": {"name": "🎬 Vidyakul", "icon": "🎬"},
    "aakash": {"name": "🏆 Aakash", "icon": "🏆"},
    "khanglobal": {"name": "🌍 Khan Global Studies", "icon": "🌍"},
    "targetwithankit": {"name": "🎯 Target with Ankit", "icon": "🎯"},
    "edurev": {"name": "📚 EduRev", "icon": "📚"},
    "selectionway": {"name": "🛣️ Selection Way", "icon": "🛣️"},
    "parmaarssc": {"name": "📋 Parmaar SSC", "icon": "📋"},
    "sscmaker": {"name": "🔧 SSC Maker", "icon": "🔧"},
    "smartkida": {"name": "🧩 SmartKida", "icon": "🧩"},
}

@Client.on_message(filters.command("login"))
async def login_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        await message.reply_text("🔒 **Bot is locked!** Contact owner.")
        return
    
    # Check premium or free limit
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await message.reply_text(
            "⚠️ **Premium Feature!**\n\n"
            "Login and batch download features require premium access.\n\n"
            "**Free Users Can:**\n"
            "• Send direct video/PDF links (10 per day)\n\n"
            "**Premium Users Get:**\n"
            "• App login access\n"
            "• Batch downloads via TXT\n"
            "• Unlimited downloads\n\n"
            "Contact owner for premium!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
            ])
        )
        return
    
    # Show coaching apps menu
    await show_apps_menu(message)

async def show_apps_menu(message):
    """Display all coaching apps"""
    buttons = []
    row = []
    
    # Create 2-column layout
    for app_id, app_data in COACHING_APPS.items():
        btn_text = f"{app_data['icon']} {app_data['name'].split(' ', 1)[1]}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"app_{app_id}"))
        
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="start")])
    
    await message.reply_text(
        "📚 **Select Your Coaching Platform:**\n\n"
        "Choose the app you want to login to and download content from:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^login_menu$"))
async def login_menu_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    
    # Check premium
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await query.answer("⚠️ Premium required!", show_alert=True)
        return
    
    # Clear any existing state
    clear_user_state(user_id)
    
    # Show apps menu
    buttons = []
    row = []
    
    for app_id, app_data in COACHING_APPS.items():
        btn_text = f"{app_data['icon']} {app_data['name'].split(' ', 1)[1]}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"app_{app_id}"))
        
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="start")])
    
    await query.message.edit_text(
        "📚 **Select Your Coaching Platform:**\n\n"
        "Choose the app you want to login to:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_name = COACHING_APPS[app_id]["name"]
    user_id = query.from_user.id
    
    # Set user state to waiting for phone number
    set_user_state(user_id, 'awaiting_phone', {'app_id': app_id, 'app_name': app_name})
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n\n"
        f"📞 **Please send your phone number:**\n\n"
        f"**Examples:**\n"
        f"• `+919876543210`\n"
        f"• `9876543210`\n"
        f"• `919876543210`\n\n"
        f"⚠️ Send only your phone number (country code optional for India)\n"
        f"💡 Use /cancel to stop this process",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )

@Client.on_callback_query(filters.regex("^cancel_login$"))
async def cancel_login_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    clear_user_state(user_id)
    
    await query.message.edit_text(
        "❌ **Login Cancelled**\n\n"
        "You can start again anytime with /login",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
    )

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast', 'cancel']), group=1)
async def handle_user_input(client: Client, message: Message):
    """Handle user text input based on current state - PRIORITY HANDLER"""
    user_id = message.from_user.id
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    # Get user's current state
    session = get_user_state(user_id)
    state = session.get('state')
    data = session.get('data', {})
    
    # Handle based on state
    if state == 'awaiting_phone':
        await handle_phone_number(client, message, data)
    elif state == 'awaiting_otp':
        await handle_otp(client, message, data)
    elif state == 'awaiting_batch_id':
        await handle_batch_id(client, message, data)
    else:
        # No active session, let download.py handler take over
        pass

async def handle_phone_number(client: Client, message: Message, data):
    """Process phone number input"""
    user_id = message.from_user.id
    phone = message.text.strip()
    
    # Validate phone number
    phone_cleaned = re.sub(r'[^\d+]', '', phone)
    
    if len(phone_cleaned) < 10:
        await message.reply_text(
            "❌ **Invalid Phone Number!**\n\n"
            "Please send a valid phone number.\n\n"
            "**Examples:**\n"
            "• +919876543210\n"
            "• 9876543210\n\n"
            "Use /cancel to stop."
        )
        return
    
    # Add +91 if not present
    if not phone_cleaned.startswith('+'):
        if not phone_cleaned.startswith('91'):
            phone_cleaned = '+91' + phone_cleaned
        else:
            phone_cleaned = '+' + phone_cleaned
    
    # Update session
    update_user_data(user_id, 'phone', phone_cleaned)
    set_user_state(user_id, 'awaiting_otp', data)
    
    await message.reply_text(
        f"✅ **Phone Number Saved**\n\n"
        f"📱 Number: `{phone_cleaned}`\n\n"
        f"🔐 **Now enter your OTP:**\n\n"
        f"**Test OTP:** `5 7 2 0 0 2`\n"
        f"(Remove spaces: 572002)\n\n"
        f"💡 For real apps, enter the OTP you receive\n"
        f"Use /cancel to stop"
    )

async def handle_otp(client: Client, message: Message, data):
    """Process OTP input"""
    user_id = message.from_user.id
    otp = message.text.strip().replace(' ', '')
    
    # Validate OTP
    if not otp.isdigit() or len(otp) != 6:
        await message.reply_text(
            "❌ **Invalid OTP!**\n\n"
            "Please send 6-digit OTP.\n\n"
            "**Example:** 572002\n\n"
            "Use /cancel to stop."
        )
        return
    
    # Simulate OTP verification
    status_msg = await message.reply_text("🔐 **Verifying OTP...**")
    
    await asyncio.sleep(2)
    
    # For demo, accept test OTP or any 6 digits
    if otp == "572002" or len(otp) == 6:
        update_user_data(user_id, 'otp', otp)
        
        # Show demo batches
        await show_batches(client, status_msg, data)
    else:
        await status_msg.edit_text(
            "❌ **OTP Verification Failed!**\n\n"
            "Please try again with correct OTP.\n\n"
            "Use /cancel to start over."
        )

async def show_batches(client, message, data):
    """Show available batches (demo)"""
    app_name = data.get('app_name', 'Platform')
    
    # Demo batches
    batches = [
        {"id": "batch001", "name": "🎯 NEET 2024 Complete Course"},
        {"id": "batch002", "name": "📚 JEE Mains + Advanced"},
        {"id": "batch003", "name": "🏆 SSC CGL Complete Batch"},
        {"id": "batch004", "name": "💼 Bank PO Preparation"},
        {"id": "batch005", "name": "📖 UPSC Prelims + Mains"},
    ]
    
    buttons = []
    for batch in batches:
        buttons.append([InlineKeyboardButton(
            batch['name'], 
            callback_data=f"batch_{batch['id']}"
        )])
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")])
    
    await message.edit_text(
        f"✅ **Login Successful!**\n\n"
        f"📚 **{app_name}**\n\n"
        f"**Your Purchased Batches:**\n"
        f"Select a batch to generate download links:\n\n"
        f"💡 You can also send batch ID directly",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^batch_"))
async def batch_selected_callback(client: Client, query: CallbackQuery):
    batch_id = query.data.split("_")[1]
    user_id = query.from_user.id
    
    await query.message.edit_text("📝 **Generating TXT file...**")
    
    # Generate demo TXT file
    await generate_batch_txt(client, query.message, batch_id, user_id)

async def generate_batch_txt(client, message, batch_id, user_id):
    """Generate TXT file with batch content"""
    import aiofiles
    import os
    
    # Demo content
    content = f"""# Batch: {batch_id}
# Generated by Serena Lec

01. Introduction to Course | https://example.com/video1.mp4
02. What is the Internet | https://example.com/video2.mp4
03. Network Basics | https://example.com/video3.mp4
04. OSI Model Explained | https://example.com/video4.mp4
05. TCP/IP Protocol | https://example.com/video5.mp4
06. Study Material PDF | https://example.com/notes.pdf
07. Practice Questions | https://example.com/practice.pdf

# Total: 5 Videos, 2 PDFs
# Send this file back to download all content!
"""
    
    # Create downloads directory
    os.makedirs("downloads", exist_ok=True)
    
    # Save to file
    filename = f"downloads/batch_{batch_id}_{user_id}.txt"
    async with aiofiles.open(filename, 'w') as f:
        await f.write(content)
    
    # Send file
    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=(
            f"✅ **Batch TXT File Generated!**\n\n"
            f"📦 **Batch ID:** `{batch_id}`\n"
            f"🎥 **Videos:** 5\n"
            f"📄 **PDFs:** 2\n\n"
            f"**Next Steps:**\n"
            f"1. Download this TXT file\n"
            f"2. Send it back to me\n"
            f"3. I'll download and send all files!\n\n"
            f"💡 This is a demo file. For real apps, it will contain actual links."
        )
    )
    
    await message.delete()
    
    # Clear session
    clear_user_state(user_id)
    
    # Delete file
    try:
        os.remove(filename)
    except:
        pass

async def handle_batch_id(client: Client, message: Message, data):
    """Handle batch ID input"""
    batch_id = message.text.strip()
    user_id = message.from_user.id
    
    status_msg = await message.reply_text("📝 **Generating batch content...**")
    await generate_batch_txt(client, status_msg, batch_id, user_id)
