from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import Config
from utils.session import (
    set_user_state, get_user_state, clear_user_state, 
    update_user_data, get_user_data, set_api_client, get_api_client
)
from utils.platform_apis import get_platform_api
import re
import asyncio
import aiofiles
import os

# All Indian Coaching Apps
COACHING_APPS = {
    "rgvikramjeet": {"name": "🎖️ RG Vikramjeet", "icon": "🎖️", "url": "https://rankersgurukul.com"},
    "pw": {"name": "📚 Physics Wallah", "icon": "📚", "url": "https://www.pw.live"},
    "unacademy": {"name": "🎓 Unacademy", "icon": "🎓", "url": "https://unacademy.com"},
    "vedantu": {"name": "📖 Vedantu", "icon": "📖", "url": "https://www.vedantu.com"},
    "byjus": {"name": "🔬 BYJU'S", "icon": "🔬", "url": "https://byjus.com"},
    "khan": {"name": "🌟 Khan Academy", "icon": "🌟", "url": "https://www.khanacademy.org"},
    "toppr": {"name": "🎯 Toppr", "icon": "🎯", "url": "https://www.toppr.com"},
    "doubtnut": {"name": "❓ Doubtnut", "icon": "❓", "url": "https://www.doubtnut.com"},
    "carrierwill": {"name": "🚀 Carrier Will", "icon": "🚀", "url": "https://carrierwill.in"},
    "studyiq": {"name": "🧠 Study IQ", "icon": "🧠", "url": "https://www.studyiq.com"},
    "exampur": {"name": "📘 Exampur", "icon": "📘", "url": "https://exampur.com"},
    "utkarsh": {"name": "⭐ Utkarsh", "icon": "⭐", "url": "https://utkarsh.com"},
    "rojgarwithankit": {"name": "💼 Rojgar with Ankit", "icon": "💼", "url": "https://rojgarwithankit.com"},
    "vidyakul": {"name": "🎬 Vidyakul", "icon": "🎬", "url": "https://vidyakul.com"},
    "aakash": {"name": "🏆 Aakash", "icon": "🏆", "url": "https://www.aakash.ac.in"},
    "khanglobal": {"name": "🌍 Khan Global Studies", "icon": "🌍", "url": "https://khanglobalstudies.com"},
    "targetwithankit": {"name": "🎯 Target with Ankit", "icon": "🎯", "url": "https://targetwithankit.com"},
    "edurev": {"name": "📚 EduRev", "icon": "📚", "url": "https://edurev.in"},
    "selectionway": {"name": "🛣️ Selection Way", "icon": "🛣️", "url": "https://selectionway.com"},
    "parmaarssc": {"name": "📋 Parmaar SSC", "icon": "📋", "url": "https://parmaarssc.com"},
    "sscmaker": {"name": "🔧 SSC Maker", "icon": "🔧", "url": "https://sscmaker.in"},
    "smartkida": {"name": "🧩 SmartKida", "icon": "🧩", "url": "https://smartkida.com"},
}

@Client.on_message(filters.command("login"))
async def login_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        await message.reply_text("🔒 **Bot is locked!** Contact owner.")
        return
    
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await message.reply_text(
            "⚠️ **Premium Feature!**\n\n"
            "Login and batch download require premium access.\n\n"
            "**Free Users Can:**\n"
            "• Send direct video/PDF links (10/day)\n\n"
            "**Premium Users Get:**\n"
            "• Platform login + batch extraction\n"
            "• Unlimited downloads\n"
            "• M3U8 support\n\n"
            "Contact owner for premium!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
            ])
        )
        return
    
    await show_apps_menu(message)

async def show_apps_menu(message):
    """Display all coaching apps"""
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
    
    await message.reply_text(
        "📚 **Select Your Coaching Platform:**\n\n"
        "Choose the platform you want to extract content from.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^login_menu$"))
async def login_menu_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await query.answer("⚠️ Premium required!", show_alert=True)
        return
    
    clear_user_state(user_id)
    
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
        "Choose the platform you want to extract content from.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    # Initialize API client
    api_client = get_platform_api(app_id)
    set_api_client(user_id, app_id, api_client)
    
    set_user_state(user_id, 'awaiting_credentials', {
        'app_id': app_id, 
        'app_name': app_name,
        'app_url': app_url
    })
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n"
        f"🌐 Website: `{app_url}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**🔐 Login Options:**\n\n"
        f"**Option 1: Phone + OTP (Recommended)**\n"
        f"Send your phone number:\n"
        f"Example: `9876543210`\n\n"
        f"**Option 2: Phone + Password**\n"
        f"Send in this format:\n"
        f"`phone*password`\n"
        f"Example: `9876543210*mypass123`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ Use the credentials registered on **{app_name}**\n\n"
        f"Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open Website", url=app_url)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )

@Client.on_callback_query(filters.regex("^cancel_login$"))
async def cancel_login_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    clear_user_state(user_id)
    clear_api_client(user_id)
    
    await query.message.edit_text(
        "❌ **Login Cancelled**\n\n"
        "You can start again anytime with /login",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
    )

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast', 'cancel']), group=1)
async def handle_user_input(client: Client, message: Message):
    """Handle user text input based on current state"""
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    session = get_user_state(user_id)
    state = session.get('state')
    data = session.get('data', {})
    
    if state == 'awaiting_credentials':
        await handle_credentials(client, message, data)
    elif state == 'awaiting_otp':
        await handle_otp(client, message, data)
    else:
        pass

async def handle_credentials(client: Client, message: Message, data):
    """Handle phone number or phone*password input"""
    user_id = message.from_user.id
    text = message.text.strip()
    app_id = data.get('app_id')
    app_name = data.get('app_name')
    
    # Check if it's phone*password format
    if '*' in text:
        parts = text.split('*', 1)
        phone = parts[0].strip()
        password = parts[1].strip()
        
        await login_with_password(client, message, user_id, app_id, app_name, phone, password)
    else:
        # Just phone number - will send OTP
        phone = text.strip()
        await send_otp_to_phone(client, message, user_id, app_id, app_name, phone, data)

async def login_with_password(client, message, user_id, app_id, app_name, phone, password):
    """Login using phone and password"""
    status = await message.reply_text("🔐 **Logging in with password...**")
    
    # Clean phone number
    phone = re.sub(r'\D', '', phone)
    
    # Get API client
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await status.edit_text("❌ **Error:** API client not found. Please try /login again.")
        return
    
    try:
        # Login with password
        token = await api_client.login_with_password(phone, password)
        
        if token:
            await status.edit_text("✅ **Login Successful!**\n\n⏳ Fetching your batches...")
            await show_user_batches(client, message, user_id, app_id, app_name, api_client)
        else:
            await status.edit_text(
                "❌ **Login Failed!**\n\n"
                "Please check:\n"
                "• Phone number is correct\n"
                "• Password is correct\n"
                "• Account exists on platform\n\n"
                "Try again with /login"
            )
            clear_user_state(user_id)
            
    except Exception as e:
        await status.edit_text(f"❌ **Error:** {str(e)}\n\nTry again with /login")
        clear_user_state(user_id)

async def send_otp_to_phone(client, message, user_id, app_id, app_name, phone, data):
    """Send OTP to user's phone via platform API"""
    status = await message.reply_text("📱 **Sending OTP to your phone...**")
    
    # Clean phone number
    phone = re.sub(r'\D', '', phone)
    
    # Get API client
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await status.edit_text("❌ **Error:** API client not found. Please try /login again.")
        return
    
    try:
        # Send OTP via API
        otp_sent = await api_client.send_otp(phone)
        
        if otp_sent:
            update_user_data(user_id, 'phone', phone)
            set_user_state(user_id, 'awaiting_otp', data)
            
            await status.edit_text(
                f"✅ **OTP Sent Successfully!**\n\n"
                f"📱 Phone: `+91{phone}`\n"
                f"📲 Platform: **{app_name}**\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"🔐 **Check your phone for OTP**\n\n"
                f"OTP sent via SMS/App notification\n\n"
                f"**Send the OTP here:**\n"
                f"• 4-digit or 6-digit code\n"
                f"• Example: `123456` or `1234`\n\n"
                f"⏱️ OTP valid for 5-10 minutes\n\n"
                f"Use /cancel to stop"
            )
        else:
            await status.edit_text(
                "❌ **Failed to send OTP!**\n\n"
                "Possible reasons:\n"
                "• Phone number not registered\n"
                "• Platform API unavailable\n"
                "• Network issue\n\n"
                "**Try:**\n"
                "• Check phone number\n"
                "• Use phone*password format\n"
                "• Try again with /login"
            )
            clear_user_state(user_id)
            
    except Exception as e:
        await status.edit_text(f"❌ **Error:** {str(e)}\n\nTry again with /login")
        clear_user_state(user_id)

async def handle_otp(client: Client, message: Message, data):
    """Verify OTP and login"""
    user_id = message.from_user.id
    otp = message.text.strip().replace(' ', '')
    app_id = data.get('app_id')
    app_name = data.get('app_name')
    phone = get_user_data(user_id, 'phone')
    
    # Validate OTP (4 or 6 digits)
    if not otp.isdigit() or len(otp) not in [4, 6]:
        await message.reply_text(
            "❌ **Invalid OTP!**\n\n"
            "Please send 4 or 6 digit OTP.\n\n"
            "**Example:** `123456`\n\n"
            "Use /cancel to stop."
        )
        return
    
    status = await message.reply_text("🔐 **Verifying OTP...**")
    
    # Get API client
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await status.edit_text("❌ **Error:** API client not found. Please try /login again.")
        return
    
    try:
        # Verify OTP via API
        token = await api_client.verify_otp(phone, otp)
        
        if token:
            update_user_data(user_id, 'auth_token', token)
            await status.edit_text("✅ **OTP Verified!**\n\n⏳ Fetching your batches...")
            await show_user_batches(client, message, user_id, app_id, app_name, api_client)
        else:
            await status.edit_text(
                "❌ **OTP Verification Failed!**\n\n"
                "Possible reasons:\n"
                "• Wrong OTP\n"
                "• OTP expired\n"
                "• Already used\n\n"
                "Try /login again to get new OTP"
            )
            clear_user_state(user_id)
            
    except Exception as e:
        await status.edit_text(f"❌ **Error:** {str(e)}\n\nTry /login again")
        clear_user_state(user_id)

async def show_user_batches(client, message, user_id, app_id, app_name, api_client):
    """Fetch and display user's purchased batches"""
    try:
        # Get batches from API
        batches = await api_client.get_batches()
        
        if not batches:
            await message.reply_text(
                "❌ **No Batches Found!**\n\n"
                "You don't have any purchased courses on this platform.\n\n"
                "Or the API returned empty data."
            )
            clear_user_state(user_id)
            return
        
        # Create buttons
        buttons = []
        for batch in batches[:20]:  # Limit to 20 batches
            batch_id = batch.get('id') or batch.get('batch_id') or batch.get('course_id')
            batch_name = batch.get('name') or batch.get('title') or f"Batch {batch_id}"
            
            # Truncate long names
            if len(batch_name) > 40:
                batch_name = batch_name[:37] + "..."
            
            buttons.append([
                InlineKeyboardButton(
                    f"📦 {batch_name}", 
                    callback_data=f"batch_{app_id}_{batch_id}"
                )
            ])
        
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")])
        
        await message.reply_text(
            f"✅ **Login Successful!**\n\n"
            f"📚 **{app_name}**\n"
            f"📦 **Your Purchased Batches:** ({len(batches)})\n\n"
            f"Select a batch to extract content:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Update state
        update_user_data(user_id, 'batches', batches)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error fetching batches:** {str(e)}")
        clear_user_state(user_id)

@Client.on_callback_query(filters.regex("^batch_"))
async def batch_selected_callback(client: Client, query: CallbackQuery):
    """Handle batch selection"""
    user_id = query.from_user.id
    
    # Parse callback data
    parts = query.data.split("_")
    app_id = parts[1]
    batch_id = "_".join(parts[2:])  # In case batch_id has underscores
    
    await query.message.edit_text(
        f"📝 **Extracting batch content...**\n\n"
        f"⏳ This may take a few moments..."
    )
    
    # Get API client
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await query.message.edit_text("❌ **Session expired!** Use /login again.")
        return
    
    try:
        # Get batch content from API
        content = await api_client.get_batch_content(batch_id)
        
        if not content:
            await query.message.edit_text(
                "❌ **No content found in this batch!**\n\n"
                "The batch might be empty or API error occurred."
            )
            return
        
        # Generate TXT file
        await generate_batch_txt_file(client, query.message, user_id, app_id, batch_id, content)
        
    except Exception as e:
        await query.message.edit_text(f"❌ **Error:** {str(e)}")

async def generate_batch_txt_file(client, message, user_id, app_id, batch_id, content):
    """Generate TXT file with all batch content links"""
    try:
        app_name = COACHING_APPS.get(app_id, {}).get('name', 'Platform')
        
        # Parse content and extract links
        lines = []
        video_count = 0
        pdf_count = 0
        
        for item in content:
            # Extract title
            title = (
                item.get('title') or 
                item.get('name') or 
                item.get('lecture_name') or 
                f"Content {len(lines) + 1}"
            )
            
            # Extract URL (video or PDF)
            url = (
                item.get('video_url') or 
                item.get('url') or 
                item.get('link') or 
                item.get('m3u8_url') or
                item.get('hls_url') or
                item.get('stream_url') or
                item.get('pdf_url')
            )
            
            if url:
                # Clean title
                title = title.replace('|', '-').strip()
                
                # Determine type
                if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.mkv', 'video']):
                    video_count += 1
                elif '.pdf' in url.lower():
                    pdf_count += 1
                
                lines.append(f"{title} | {url}")
        
        if not lines:
            await message.edit_text(
                "❌ **No downloadable links found!**\n\n"
                "The batch content doesn't contain video/PDF URLs."
            )
            return
        
        # Create TXT content
        txt_content = f"# Batch Content - {app_name}\n"
        txt_content += f"# Batch ID: {batch_id}\n"
        txt_content += f"# Videos: {video_count} | PDFs: {pdf_count}\n"
        txt_content += f"# Total Items: {len(lines)}\n"
        txt_content += f"# Generated by Serena Lec Bot\n\n"
        txt_content += "\n".join(lines)
        
        # Save to file
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/batch_{user_id}_{int(asyncio.get_event_loop().time())}.txt"
        
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(txt_content)
        
        # Send file
        await client.send_document(
            chat_id=message.chat.id,
            document=filename,
            caption=(
                f"✅ **Batch TXT File Generated!**\n\n"
                f"📚 **Platform:** {app_name}\n"
                f"📦 **Batch ID:** `{batch_id}`\n"
                f"🎥 **Videos:** {video_count}\n"
                f"📄 **PDFs:** {pdf_count}\n"
                f"📊 **Total:** {len(lines)}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"**📥 Next Steps:**\n"
                f"1. This file contains all download links\n"
                f"2. **Send this file back to me**\n"
                f"3. I'll download all videos/PDFs!\n\n"
                f"✨ **M3U8 videos will be converted to MP4**"
            )
        )
        
        await message.delete()
        
        # Clear session
        clear_user_state(user_id)
        clear_api_client(user_id)
        
        # Delete file
        try:
            os.remove(filename)
        except:
            pass
        
    except Exception as e:
        await message.edit_text(f"❌ **Error generating TXT:** {str(e)}")
        print(f"TXT Generation Error: {e}")
