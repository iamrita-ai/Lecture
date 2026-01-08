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
import time

# All Indian Coaching Apps
COACHING_APPS = {
    "rgvikramjeet": {"name": "🎖️ RG Vikramjeet", "icon": "🎖️", "url": "https://rankersgurukul.com"},
    "pw": {"name": "📚 Physics Wallah", "icon": "📚", "url": "https://www.pw.live"},
    "unacademy": {"name": "🎓 Unacademy", "icon": "🎓", "url": "https://unacademy.com"},
    "vedantu": {"name": "📖 Vedantu", "icon": "📖", "url": "https://www.vedantu.com"},
    "carrierwill": {"name": "🚀 Carrier Will", "icon": "🚀", "url": "https://carrierwill.in"},
    "studyiq": {"name": "🧠 Study IQ", "icon": "🧠", "url": "https://www.studyiq.com"},
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
            "Login requires premium.\n\n"
            "Contact owner!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
            ])
        )
        return
    
    await show_apps_menu(message)

async def show_apps_menu(message):
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
        "📚 **Select Your Platform:**",
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
        "📚 **Select Your Platform:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    buttons = [
        [InlineKeyboardButton("🔐 Auto Login", callback_data=f"auto_{app_id}")],
        [InlineKeyboardButton("📋 Manual Extraction", callback_data=f"manual_{app_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="start")]
    ]
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n\n"
        f"**Choose Method:**\n\n"
        f"🔐 **Auto:** Bot tries to login\n"
        f"📋 **Manual:** You extract links yourself\n\n"
        f"Recommended: Manual (100% working)",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^auto_"))
async def auto_login_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_data = COACHING_APPS[app_id]
    app_name = app_data["name"]
    app_url = app_data["url"]
    user_id = query.from_user.id
    
    api_client = get_platform_api(app_id)
    set_api_client(user_id, app_id, api_client)
    
    set_user_state(user_id, 'awaiting_phone', {
        'app_id': app_id, 
        'app_name': app_name,
        'app_url': app_url
    })
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n\n"
        f"**Step 1: Phone Number**\n\n"
        f"Send your phone:\n"
        f"Example: `9876543210`\n\n"
        f"Use /cancel to stop",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )

@Client.on_callback_query(filters.regex("^manual_"))
async def manual_extraction_callback(client: Client, query: CallbackQuery):
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
        f"📱 **{app_name} - Manual**\n\n"
        f"**Steps:**\n"
        f"1. Open {app_url}\n"
        f"2. Login yourself\n"
        f"3. Play a video\n"
        f"4. Press F12 → Network\n"
        f"5. Find .m3u8 link\n"
        f"6. Send here:\n\n"
        f"`Title | http://link.m3u8`\n\n"
        f"Type /done when finished",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open", url=app_url)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
        ])
    )

@Client.on_callback_query(filters.regex("^cancel_login$"))
async def cancel_login_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    clear_user_state(user_id)
    
    await query.message.edit_text(
        "❌ **Cancelled**\n\nUse /login to restart",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
    )

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast', 'cancel', 'done']), group=1)
async def handle_user_input(client: Client, message: Message):
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
    elif state == 'awaiting_batch_links':
        await handle_batch_links(client, message, data)

async def handle_phone_number(client: Client, message: Message, data):
    user_id = message.from_user.id
    phone = message.text.strip()
    app_name = data.get('app_name', 'Platform')
    
    phone = re.sub(r'\D', '', phone)
    
    if len(phone) < 10:
        await message.reply_text("❌ **Invalid phone!**\nSend 10-digit number")
        return
    
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
    
    update_user_data(user_id, 'phone', phone)
    set_user_state(user_id, 'awaiting_password', data)
    
    await message.reply_text(
        f"✅ **Phone Saved:** `{phone}`\n\n"
        f"**Step 2: Password**\n\n"
        f"Send your {app_name} password:"
    )

async def handle_password(client: Client, message: Message, data):
    user_id = message.from_user.id
    password = message.text.strip()
    app_id = data.get('app_id')
    app_name = data.get('app_name')
    phone = get_user_data(user_id, 'phone')
    
    try:
        await message.delete()
    except:
        pass
    
    status = await message.reply_text(f"🔐 **Logging in to {app_name}...**")
    
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await status.edit_text("❌ **Error:** Use /login again")
        clear_user_state(user_id)
        return
    
    try:
        token = await api_client.login_with_password(phone, password)
        
        if token:
            update_user_data(user_id, 'auth_token', token)
            await status.edit_text("✅ **Login Success!**\n\n⏳ Fetching batches...")
            await asyncio.sleep(1)
            await fetch_batches(client, status, user_id, app_id, app_name, api_client)
        else:
            await status.edit_text(
                "❌ **Login Failed!**\n\n"
                "Check credentials and try again.\n\n"
                "Or use Manual method instead.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Retry", callback_data=f"app_{app_id}")],
                    [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
                ])
            )
            clear_user_state(user_id)
    except Exception as e:
        await status.edit_text(
            f"❌ **Error:** `{str(e)}`\n\n"
            f"API may not be available.\n"
            f"Use Manual method instead.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Manual", callback_data=f"manual_{app_id}")],
                [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
            ])
        )
        clear_user_state(user_id)

async def fetch_batches(client, message, user_id, app_id, app_name, api_client):
    try:
        batches = await api_client.get_batches()
        
        if not batches:
            await message.edit_text("❌ **No batches found!**")
            clear_user_state(user_id)
            return
        
        buttons = []
        for batch in batches[:20]:
            batch_id = batch.get('id') or batch.get('batch_id') or batch.get('_id')
            batch_name = batch.get('name') or batch.get('title') or f"Batch {batch_id}"
            
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
            f"✅ **{app_name}**\n\n"
            f"**Your Batches:** ({len(batches)})\n\n"
            f"Select one:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await message.edit_text(f"❌ **Error:** `{str(e)}`")
        clear_user_state(user_id)

@Client.on_callback_query(filters.regex("^batch_"))
async def batch_selected_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    parts = query.data.split("_")
    app_id = parts[1]
    batch_id = "_".join(parts[2:])
    
    await query.message.edit_text(f"📝 **Extracting batch...**\n\n⏳ Please wait...")
    
    api_client = get_api_client(user_id, app_id)
    if not api_client:
        await query.message.edit_text("❌ **Session expired!** Use /login again")
        return
    
    try:
        content = await api_client.get_batch_content(batch_id)
        
        if not content:
            await query.message.edit_text("❌ **No content found!**")
            return
        
        await generate_txt(client, query.message, user_id, app_id, batch_id, content)
    except Exception as e:
        await query.message.edit_text(f"❌ **Error:** `{str(e)}`")

async def generate_txt(client, message, user_id, app_id, batch_id, content):
    try:
        app_name = COACHING_APPS.get(app_id, {}).get('name', 'Platform')
        
        lines = []
        video_count = 0
        pdf_count = 0
        
        for item in content:
            title = item.get('title') or item.get('name') or f"Content {len(lines)+1}"
            url = (
                item.get('video_url') or item.get('url') or 
                item.get('m3u8_url') or item.get('hls_url') or 
                item.get('pdf_url')
            )
            
            if url:
                title = title.replace('|', '-').strip()
                
                if '.m3u8' in url or '.mp4' in url:
                    video_count += 1
                elif '.pdf' in url:
                    pdf_count += 1
                
                lines.append(f"{title} | {url}")
        
        if not lines:
            await message.edit_text("❌ **No links found!**")
            return
        
        txt_content = f"# {app_name} - Batch {batch_id}\n"
        txt_content += f"# Videos: {video_count} | PDFs: {pdf_count}\n\n"
        txt_content += "\n".join(lines)
        
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/batch_{user_id}_{int(time.time())}.txt"
        
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(txt_content)
        
        await client.send_document(
            chat_id=message.chat.id,
            document=filename,
            caption=(
                f"✅ **Batch TXT!**\n\n"
                f"🎥 Videos: {video_count}\n"
                f"📄 PDFs: {pdf_count}\n\n"
                f"**Send this back to download!**"
            )
        )
        
        await message.delete()
        clear_user_state(user_id)
        
        try:
            os.remove(filename)
        except:
            pass
    except Exception as e:
        await message.edit_text(f"❌ **Error:** `{str(e)}`")

async def handle_batch_links(client: Client, message: Message, data):
    user_id = message.from_user.id
    text = message.text.strip()
    
    session = get_user_state(user_id)
    collected = session['data'].get('collected_links', [])
    
    if '|' in text:
        lines = text.split('\n')
        added = 0
        for line in lines:
            line = line.strip()
            if '|' in line:
                collected.append(line)
                added += 1
        
        update_user_data(user_id, 'collected_links', collected)
        await message.reply_text(
            f"✅ **{added} link(s) added!**\n\n"
            f"Total: {len(collected)}\n\n"
            f"Send more or type /done"
        )
    elif text.startswith('http'):
        title = f"Video {len(collected)+1}"
        collected.append(f"{title} | {text}")
        update_user_data(user_id, 'collected_links', collected)
        await message.reply_text(f"✅ **Added!** Total: {len(collected)}\n\nSend more or /done")
    else:
        await message.reply_text("❌ **Invalid!**\n\nFormat: `Title | URL`\n\nOr type /done")

@Client.on_message(filters.command("done"))
async def done_command(client: Client, message: Message):
    user_id = message.from_user.id
    session = get_user_state(user_id)
    
    if session.get('state') == 'awaiting_batch_links':
        data = session.get('data', {})
        await create_txt_from_links(client, message, user_id, data)
    else:
        await message.reply_text("❌ **No active collection!**\n\nUse /login")

async def create_txt_from_links(client, message, user_id, data):
    session = get_user_state(user_id)
    collected = session['data'].get('collected_links', [])
    
    if not collected:
        await message.reply_text("❌ **No links!** Send at least one.")
        return
    
    app_name = data.get('app_name', 'Platform')
    
    status = await message.reply_text("📝 **Generating...**")
    
    video_count = sum(1 for l in collected if '.m3u8' in l or '.mp4' in l)
    pdf_count = sum(1 for l in collected if '.pdf' in l)
    
    content = f"# {app_name} Batch\n"
    content += f"# Videos: {video_count} | PDFs: {pdf_count}\n\n"
    content += "\n".join(collected)
    
    os.makedirs("downloads", exist_ok=True)
    filename = f"downloads/batch_{user_id}_{int(time.time())}.txt"
    
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(content)
    
    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=(
            f"✅ **TXT Generated!**\n\n"
            f"🎥 Videos: {video_count}\n"
            f"📄 PDFs: {pdf_count}\n\n"
            f"**Send this back to download!**"
        )
    )
    
    await status.delete()
    clear_user_state(user_id)
    
    try:
        os.remove(filename)
    except:
        pass
