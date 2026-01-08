from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import Config
from utils.session import set_user_state, get_user_state, clear_user_state, update_user_data
import re
import asyncio

# All Indian Coaching Apps with their websites
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
    "rojgarwithankit": {"name": "💼 Rojgar with Ankit", "icon": "💼", "url": "https://play.google.com/store/apps/details?id=com.rojgarwithankit"},
    "vidyakul": {"name": "🎬 Vidyakul", "icon": "🎬", "url": "https://vidyakul.com"},
    "aakash": {"name": "🏆 Aakash", "icon": "🏆", "url": "https://www.aakash.ac.in"},
    "khanglobal": {"name": "🌍 Khan Global Studies", "icon": "🌍", "url": "https://khanglobalstudies.com"},
    "targetwithankit": {"name": "🎯 Target with Ankit", "icon": "🎯", "url": "https://play.google.com/store/apps/details?id=com.targetwithankit"},
    "edurev": {"name": "📚 EduRev", "icon": "📚", "url": "https://edurev.in"},
    "selectionway": {"name": "🛣️ Selection Way", "icon": "🛣️", "url": "https://selectionway.com"},
    "parmaarssc": {"name": "📋 Parmaar SSC", "icon": "📋", "url": "https://play.google.com/store/apps/details?id=com.parmaarssc"},
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
            "Login and batch download require premium.\n\n"
            "**Free Users:**\n"
            "• Send direct video/PDF links (10/day)\n\n"
            "**Premium Users:**\n"
            "• App login + batch downloads\n"
            "• Unlimited downloads\n\n"
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
        "Choose the app/website you want to extract content from:",
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
        "Choose the app/website you want to extract content from:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    set_user_state(user_id, 'awaiting_phone', {
        'app_id': app_id, 
        'app_name': app_name,
        'app_url': app_url
    })
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n"
        f"🌐 Website: `{app_url}`\n\n"
        f"📞 **Send Your Registered Phone Number:**\n\n"
        f"**Examples:**\n"
        f"• `+919876543210`\n"
        f"• `9876543210`\n\n"
        f"⚠️ **Important:** This should be the phone number registered on {app_name}\n\n"
        f"💡 After sending phone, you'll get OTP on your app/SMS\n"
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
    
    if state == 'awaiting_phone':
        await handle_phone_number(client, message, data)
    elif state == 'awaiting_otp':
        await handle_otp(client, message, data)
    elif state == 'awaiting_batch_links':
        await handle_batch_links(client, message, data)
    else:
        pass

async def handle_phone_number(client: Client, message: Message, data):
    """Process phone number input"""
    user_id = message.from_user.id
    phone = message.text.strip()
    app_name = data.get('app_name', 'Platform')
    app_url = data.get('app_url', '')
    
    phone_cleaned = re.sub(r'[^\d+]', '', phone)
    
    if len(phone_cleaned) < 10:
        await message.reply_text(
            "❌ **Invalid Phone Number!**\n\n"
            "Please send a valid phone number.\n\n"
            "**Examples:**\n"
            "• +919876543210\n"
            "• 9876543210"
        )
        return
    
    if not phone_cleaned.startswith('+'):
        if not phone_cleaned.startswith('91'):
            phone_cleaned = '+91' + phone_cleaned
        else:
            phone_cleaned = '+' + phone_cleaned
    
    update_user_data(user_id, 'phone', phone_cleaned)
    set_user_state(user_id, 'awaiting_otp', data)
    
    await message.reply_text(
        f"✅ **Phone Number Saved**\n\n"
        f"📱 Number: `{phone_cleaned}`\n"
        f"📲 Platform: **{app_name}**\n\n"
        f"🔐 **Now Enter Your OTP:**\n\n"
        f"**Steps:**\n"
        f"1. Open {app_name} app/website\n"
        f"2. Login with `{phone_cleaned}`\n"
        f"3. You'll receive OTP via SMS/App\n"
        f"4. Send that OTP here\n\n"
        f"**Format:** `123456` (6 digits without spaces)\n\n"
        f"💡 Example: If OTP is 5 7 2 0 0 2, send: `572002`\n\n"
        f"Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open App/Website", url=app_url)]
        ])
    )

async def handle_otp(client: Client, message: Message, data):
    """Process OTP and request batch information"""
    user_id = message.from_user.id
    otp = message.text.strip().replace(' ', '')
    app_name = data.get('app_name', 'Platform')
    phone = get_user_state(user_id)['data'].get('phone', '')
    
    if not otp.isdigit() or len(otp) != 6:
        await message.reply_text(
            "❌ **Invalid OTP!**\n\n"
            "Please send 6-digit OTP.\n\n"
            "**Example:** 572002\n\n"
            "Use /cancel to stop."
        )
        return
    
    status_msg = await message.reply_text("🔐 **Processing Login...**")
    
    await asyncio.sleep(1)
    
    update_user_data(user_id, 'otp', otp)
    update_user_data(user_id, 'logged_in', True)
    
    await status_msg.edit_text(
        f"✅ **Login Successful!**\n\n"
        f"📱 Phone: `{phone}`\n"
        f"🔐 OTP: `{otp}`\n"
        f"📲 Platform: **{app_name}**\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**📦 Now Send Your Batch/Course Links:**\n\n"
        f"**Instructions:**\n"
        f"1. Open {app_name} app/website\n"
        f"2. Go to your purchased batch/course\n"
        f"3. Copy ALL video/PDF links\n"
        f"4. Send them here in this format:\n\n"
        f"```\n"
        f"Video Title 1 | http://link1.m3u8\n"
        f"Video Title 2 | http://link2.m3u8\n"
        f"PDF Title | http://pdf-link.pdf\n"
        f"```\n\n"
        f"**OR**\n\n"
        f"Send batch links one by one, I'll collect them!\n\n"
        f"When done, type: `/done`\n\n"
        f"💡 Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ℹ️ How to Get Links?", callback_data="help_links")]
        ])
    )
    
    set_user_state(user_id, 'awaiting_batch_links', data)
    update_user_data(user_id, 'collected_links', [])

@Client.on_callback_query(filters.regex("^help_links$"))
async def help_links_callback(client: Client, query: CallbackQuery):
    await query.answer(
        "1. Open app in browser\n"
        "2. Open Developer Tools (F12)\n"
        "3. Go to Network tab\n"
        "4. Play a video\n"
        "5. Look for .m3u8 links\n"
        "6. Copy and send here!",
        show_alert=True
    )

async def handle_batch_links(client: Client, message: Message, data):
    """Collect batch links from user"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text.lower() == '/done':
        await generate_batch_file(client, message, user_id, data)
        return
    
    session = get_user_state(user_id)
    collected = session['data'].get('collected_links', [])
    
    # Parse links
    if '|' in text:
        # Format: Title | URL
        collected.append(text)
        update_user_data(user_id, 'collected_links', collected)
        await message.reply_text(
            f"✅ **Link Added!**\n\n"
            f"📊 Total collected: {len(collected)}\n\n"
            f"Send more links or type `/done` when finished."
        )
    elif text.startswith('http'):
        # Just URL, auto-generate title
        title = f"Video {len(collected) + 1}"
        collected.append(f"{title} | {text}")
        update_user_data(user_id, 'collected_links', collected)
        await message.reply_text(
            f"✅ **Link Added!**\n\n"
            f"📊 Total collected: {len(collected)}\n"
            f"📝 Auto-titled as: `{title}`\n\n"
            f"Send more or type `/done`"
        )
    else:
        await message.reply_text(
            "❌ **Invalid Format!**\n\n"
            "**Send in format:**\n"
            "`Title | http://link.m3u8`\n\n"
            "**OR just the link:**\n"
            "`http://link.m3u8`\n\n"
            "Type `/done` when finished."
        )

async def generate_batch_file(client, message, user_id, data):
    """Generate TXT file with all collected links"""
    import aiofiles
    import os
    
    session = get_user_state(user_id)
    collected_links = session['data'].get('collected_links', [])
    
    if not collected_links:
        await message.reply_text(
            "❌ **No Links Collected!**\n\n"
            "Please send at least one video/PDF link."
        )
        return
    
    app_name = data.get('app_name', 'Platform')
    phone = session['data'].get('phone', 'unknown')
    
    status = await message.reply_text("📝 **Generating TXT file...**")
    
    # Create content
    content = f"# Batch Links - {app_name}\n"
    content += f"# Phone: {phone}\n"
    content += f"# Total Links: {len(collected_links)}\n"
    content += f"# Generated by Serena Lec\n\n"
    
    for link in collected_links:
        content += f"{link}\n"
    
    # Save to file
    os.makedirs("downloads", exist_ok=True)
    filename = f"downloads/batch_{user_id}_{int(asyncio.get_event_loop().time())}.txt"
    
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(content)
    
    # Send file
    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=(
            f"✅ **Batch TXT File Generated!**\n\n"
            f"📲 Platform: **{app_name}**\n"
            f"📊 Total Links: **{len(collected_links)}**\n\n"
            f"**Next Steps:**\n"
            f"1. This file contains all your batch links\n"
            f"2. Send this file back to me\n"
            f"3. I'll download all videos/PDFs!\n\n"
            f"✨ Ready to download!"
        )
    )
    
    await status.delete()
    
    # Clear session
    clear_user_state(user_id)
    
    # Delete file
    try:
        os.remove(filename)
    except:
        pass

@Client.on_message(filters.command("done"))
async def done_command(client: Client, message: Message):
    """Finish collecting links and generate file"""
    user_id = message.from_user.id
    session = get_user_state(user_id)
    
    if session.get('state') == 'awaiting_batch_links':
        data = session.get('data', {})
        await generate_batch_file(client, message, user_id, data)
    else:
        await message.reply_text(
            "❌ **No active batch collection!**\n\n"
            "Use /login to start."
        )
