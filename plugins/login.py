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
    "carrierwill": {"name": "🚀 Carrier Will", "icon": "🚀", "url": "https://carrierwill.in"},
    "studyiq": {"name": "🧠 Study IQ", "icon": "🧠", "url": "https://www.studyiq.com"},
    "exampur": {"name": "📘 Exampur", "icon": "📘", "url": "https://exampur.com"},
    "utkarsh": {"name": "⭐ Utkarsh", "icon": "⭐", "url": "https://utkarsh.com"},
    "rojgarwithankit": {"name": "💼 Rojgar with Ankit", "icon": "💼", "url": "https://rojgarwithankit.com"},
    "vidyakul": {"name": "🎬 Vidyakul", "icon": "🎬", "url": "https://vidyakul.com"},
    "aakash": {"name": "🏆 Aakash", "icon": "🏆", "url": "https://www.aakash.ac.in"},
    "targetwithankit": {"name": "🎯 Target with Ankit", "icon": "🎯", "url": "https://targetwithankit.com"},
    "edurev": {"name": "📚 EduRev", "icon": "📚", "url": "https://edurev.in"},
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
            "Login and batch download require premium.\n\n"
            "**Free Users:**\n"
            "• Send direct M3U8/video links (10/day)\n\n"
            "**Premium:**\n"
            "• Platform login\n"
            "• Batch extraction\n"
            "• Unlimited downloads\n\n"
            "Contact owner!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
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
        "Choose the platform you want to login to.",
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
        "Choose the platform you want to login to.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    # Show login options
    buttons = [
        [InlineKeyboardButton("🔐 Auto Login (Password)", callback_data=f"auto_{app_id}")],
        [InlineKeyboardButton("📋 Manual Link Extraction", callback_data=f"manual_{app_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="start")]
    ]
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n"
        f"🌐 Website: `{app_url}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**Choose Login Method:**\n\n"
        f"🔐 **Auto Login:**\n"
        f"Bot will try to login automatically\n"
        f"(May not work if API is not public)\n\n"
        f"📋 **Manual Extraction:**\n"
        f"You login on website yourself\n"
        f"Extract M3U8 links manually\n"
        f"Send links to bot\n"
        f"(100% Working Method)\n\n"
        f"Choose your preferred method:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^auto_"))
async def auto_login_callback(client: Client, query: CallbackQuery):
    """Auto login flow"""
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    # Initialize API client
    api_client = get_platform_api(app_id)
    set_api_client(user_id, app_id, api_client)
    
    set_user_state(user_id, 'awaiting_phone', {
        'app_id': app_id, 
        'app_name': app_name,
        'app_url': app_url
    })
    
    await query.message.edit_text(
        f"📱 **{app_name} - Auto Login**\n\n"
        f"**Step 1: Phone Number**\n\n"
        f"📞 Send your registered phone number:\n\n"
        f"**Examples:**\n"
        f"• `9876543210`\n"
        f"• `+919876543210`\n\n"
        f"Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )

@Client.on_callback_query(filters.regex("^manual_"))
async def manual_extraction_callback(client: Client, query: CallbackQuery):
    """Manual link extraction flow"""
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    set_user_state(user_id, 'awaiting_batch_links', {
        'app_id': app_id, 
        'app_name': app_name,
        'app_url': app_url
    })
    
    update_user_data(user_id, 'collected_links', [])
    
    await query.message.edit_text(
        f"📱 **{app_name} - Manual Extraction**\n\n"
        f"🌐 Website: `{app_url}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**📖 Step-by-Step Guide:**\n\n"
        f"**1.** Open {app_name} in Chrome\n"
        f"**2.** Login with your credentials\n"
        f"**3.** Go to your batch\n"
        f"**4.** Open any video\n"
        f"**5.** Press `F12` (Developer Tools)\n"
        f"**6.** Go to **Network** tab\n"
        f"**7.** Play the video\n"
        f"**8.** Look for `.m3u8` links\n"
        f"**9.** Right-click → Copy link\n"
        f"**10.** Send here in format:\n\n"
        f"```\n"
        f"Lecture 1 | http://domain.com/video.m3u8\n"
        f"Lecture 2 | http://domain.com/video2.m3u8\n"
        f"```\n\n"
        f"Send links one by one or multiple together.\n"
        f"Type `/done` when finished!\n\n"
        f"Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open Website", url=app_url)],
            [InlineKeyboardButton("📺 Video Tutorial", url="https://www.youtube.com/watch?v=example")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )
@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast', 'cancel', 'done']), group=1)
async def handle_user_input(client: Client, message: Message):
    """Handle user text input based on state"""
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    session = get_user_state(user_id)
    state = session.get('state')
    data = session.get('data', {})
    
    if state == 'awaiting_phone':
        await handle_phone_number(client, message, data)
    elif state == 'awaiting_password':
        await handle_password(client, message, data)
    else:
        pass

async def handle_phone_number(client: Client, message: Message, data):
    """Handle phone number input"""
    user_id = message.from_user.id
    phone = message.text.strip()
    app_name = data.get('app_name', 'Platform')
    app_url = data.get('app_url', '')
    
    # Clean phone number
    phone = re.sub(r'\D', '', phone)
    
    # Validate
    if len(phone) < 10:
        await message.reply_text(
            "❌ **Invalid Phone Number!**\n\n"
            "Please send a valid 10-digit phone number.\n\n"
            "**Examples:**\n"
            "• 9876543210\n"
            "• +919876543210"
        )
        return
    
    # Add country code if needed
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
    
    # Save phone and ask for password
    update_user_data(user_id, 'phone', phone)
    set_user_state(user_id, 'awaiting_password', data)
    
    await message.reply_text(
        f"✅ **Phone Number Saved**\n\n"
        f"📱 Number: `{phone}`\n"
        f"📲 Platform: **{app_name}**\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**Step 2: Password**\n\n"
        f"🔐 Now send your **{app_name}** password:\n\n"
        f"**Example:** `mypassword123`\n\n"
        f"⚠️ Make sure it's the correct password for this account\n\n"
        f"🔒 Your password is secure and will not be stored\n\n"
        f"Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Forgot Password?", url=app_url)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )

async def handle_password(client: Client, message: Message, data):
    """Handle password and login"""
    user_id = message.from_user.id
    password = message.text.strip()
    app_id = data.get('app_id')
    app_name = data.get('app_name')
    phone = get_user_data(user_id, 'phone')
    
    # Delete user's password message for security
    try:
        await message.delete()
    except:
        pass
    
    status = await message.reply_text(
        "🔐 **Logging in...**\n\n"
        f"📱 Phone: `{phone}`\n"
        f"📲 Platform: **{app_name}**\n\n"
        f"⏳ Please wait..."
    )
    
    # Get API client
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await status.edit_text("❌ **Error:** Session expired. Use /login again.")
        clear_user_state(user_id)
        return
    
    try:
        # Login via API
        token = await api_client.login_with_password(phone, password)
        
        if token:
            update_user_data(user_id, 'auth_token', token)
            await status.edit_text(
                "✅ **Login Successful!**\n\n"
                f"📱 Phone: `{phone}`\n"
                f"📲 Platform: **{app_name}**\n\n"
                f"⏳ Fetching your batches..."
            )
            await asyncio.sleep(1)
            await fetch_and_show_batches(client, status, user_id, app_id, app_name, api_client)
        else:
            await status.edit_text(
                "❌ **Login Failed!**\n\n"
                "**Possible Reasons:**\n"
                "• Wrong phone number\n"
                "• Wrong password\n"
                "• Account doesn't exist\n"
                "• Platform API is down\n\n"
                "**What to do:**\n"
                "1. Check your credentials on the website\n"
                "2. Make sure you can login manually\n"
                "3. Try /login again with correct details\n\n"
                "**Need Help?**\n"
                "Contact owner if issue persists",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"app_{app_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
                ])
            )
            clear_user_state(user_id)
            
    except Exception as e:
        await status.edit_text(
            f"❌ **Login Error!**\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"**This might mean:**\n"
            f"• Platform API changed\n"
            f"• Network issue\n"
            f"• Server problem\n\n"
            f"Try /login again or contact owner",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"app_{app_id}")],
                [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
            ])
        )
        clear_user_state(user_id)
        print(f"Login error for {app_name}: {e}")

async def fetch_and_show_batches(client, message, user_id, app_id, app_name, api_client):
    """Fetch and display user batches"""
    try:
        # Fetch batches from API
        batches = await api_client.get_batches()
        
        if not batches:
            await message.edit_text(
                "❌ **No Batches Found!**\n\n"
                "**Possible Reasons:**\n"
                "• No purchased courses\n"
                "• API returned empty data\n"
                "• Account has no active subscriptions\n\n"
                "Check your account on the website",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 Check Website", url=COACHING_APPS[app_id]['url'])],
                    [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
                ])
            )
            clear_user_state(user_id)
            return
        
        # Create batch buttons
        buttons = []
        for batch in batches[:20]:  # Limit 20
            batch_id = batch.get('id') or batch.get('batch_id') or batch.get('course_id') or batch.get('_id')
            batch_name = batch.get('name') or batch.get('title') or batch.get('course_name') or f"Batch {batch_id}"
            
            # Truncate long names
            if len(batch_name) > 35:
                batch_name = batch_name[:32] + "..."
            
            buttons.append([
                InlineKeyboardButton(
                    f"📦 {batch_name}", 
                    callback_data=f"batch_{app_id}_{batch_id}"
                )
            ])
        
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")])
        
        await message.edit_text(
            f"✅ **Login Successful!**\n\n"
            f"📚 **{app_name}**\n"
            f"📦 **Your Batches:** ({len(batches)})\n\n"
            f"Select a batch to extract content:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Save batches in session
        update_user_data(user_id, 'batches', batches)
        
    except Exception as e:
        await message.edit_text(
            f"❌ **Error Fetching Batches!**\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"Try /login again",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"app_{app_id}")],
                [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
            ])
        )
        clear_user_state(user_id)
        print(f"Fetch batches error: {e}")

@Client.on_callback_query(filters.regex("^batch_"))
async def batch_selected_callback(client: Client, query: CallbackQuery):
    """Handle batch selection"""
    user_id = query.from_user.id
    
    # Parse data
    parts = query.data.split("_")
    app_id = parts[1]
    batch_id = "_".join(parts[2:])
    
    await query.message.edit_text(
        f"📝 **Extracting Batch Content...**\n\n"
        f"📦 Batch ID: `{batch_id}`\n\n"
        f"⏳ This may take a few moments..."
    )
    
    # Get API client
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await query.message.edit_text(
            "❌ **Session Expired!**\n\n"
            "Use /login again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Login Again", callback_data="login_menu")]
            ])
        )
        return
    
    try:
        # Get batch content
        content = await api_client.get_batch_content(batch_id)
        
        if not content:
            await query.message.edit_text(
                "❌ **No Content Found!**\n\n"
                "This batch might be empty or locked.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Back to Batches", callback_data=f"app_{app_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
                ])
            )
            return
        
        # Generate TXT file
        await generate_batch_txt(client, query.message, user_id, app_id, batch_id, content)
        
    except Exception as e:
        await query.message.edit_text(
            f"❌ **Error Extracting Content!**\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"Try selecting another batch",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data=f"app_{app_id}")],
                [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
            ])
        )
        print(f"Batch content error: {e}")

async def generate_batch_txt(client, message, user_id, app_id, batch_id, content):
    """Generate TXT file from batch content"""
    try:
        app_name = COACHING_APPS.get(app_id, {}).get('name', 'Platform')
        
        lines = []
        video_count = 0
        pdf_count = 0
        
        for item in content:
            # Extract title
            title = (
                item.get('title') or 
                item.get('name') or 
                item.get('lecture_name') or 
                item.get('topic') or
                f"Content {len(lines) + 1}"
            )
            
            # Extract URL
            url = (
                item.get('video_url') or 
                item.get('url') or 
                item.get('link') or 
                item.get('m3u8_url') or
                item.get('hls_url') or
                item.get('stream_url') or
                item.get('playback_url') or
                item.get('pdf_url') or
                item.get('resource_url')
            )
            
            if url:
                # Clean title
                title = title.replace('|', '-').strip()
                
                # Count types
                if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.mkv', 'video', 'stream']):
                    video_count += 1
                elif '.pdf' in url.lower() or 'pdf' in url.lower():
                    pdf_count += 1
                
                lines.append(f"{title} | {url}")
        
        if not lines:
            await message.edit_text(
                "❌ **No Downloadable Links!**\n\n"
                "The batch doesn't contain extractable video/PDF URLs.\n\n"
                "**This might mean:**\n"
                "• Content is DRM protected\n"
                "• Links are encrypted\n"
                "• API structure changed\n\n"
                "Contact owner for help",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
                ])
            )
            return
        
        # Create TXT content
        txt_content = f"# Batch Content - {app_name}\n"
        txt_content += f"# Batch ID: {batch_id}\n"
        txt_content += f"# Videos: {video_count} | PDFs: {pdf_count}\n"
        txt_content += f"# Total Items: {len(lines)}\n"
        txt_content += f"# Generated by Serena Lec Bot\n"
        txt_content += f"# Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        txt_content += "\n".join(lines)
        
        # Save file
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/batch_{user_id}_{int(asyncio.get_event_loop().time())}.txt"
        
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(txt_content)
        
        # Send file
        await client.send_document(
            chat_id=message.chat.id,
            document=filename,
            caption=(
                f"✅ **Batch TXT Generated!**\n\n"
                f"📚 **Platform:** {app_name}\n"
                f"📦 **Batch ID:** `{batch_id}`\n"
                f"🎥 **Videos:** {video_count}\n"
                f"📄 **PDFs:** {pdf_count}\n"
                f"📊 **Total:** {len(lines)}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"**📥 Next Steps:**\n"
                f"1. This file contains all links\n"
                f"2. **Send this file back to me**\n"
                f"3. I'll download all videos/PDFs\n"
                f"4. M3U8 videos → MP4 conversion\n\n"
                f"✨ Ready to download!"
            )
        )
        
        await message.delete()
        
        # Clear session
        clear_user_state(user_id)
        
        # Delete temp file
        try:
            os.remove(filename)
        except:
            pass
        
        # Log
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"#BATCH_EXTRACTED\n\n"
                f"👤 User: {message.from_user.mention if hasattr(message, 'from_user') else 'Unknown'}\n"
                f"🆔 ID: `{user_id}`\n"
                f"📚 Platform: {app_name}\n"
                f"📦 Batch: `{batch_id}`\n"
                f"🎥 Videos: {video_count}\n"
                f"📄 PDFs: {pdf_count}\n"
                f"📅 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            print(f"Log error: {e}")
        
    except Exception as e:
        await message.edit_text(
            f"❌ **Error Generating TXT!**\n\n"
            f"**Error:** `{str(e)}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Owner", url="https://t.me/technicalserena")]
            ])
        )
        print(f"TXT generation error: {e}")

import time
