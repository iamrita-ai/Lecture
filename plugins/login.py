from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import Config
from utils.session import (
    set_user_state, get_user_state, clear_user_state, 
    update_user_data, get_user_data
)
import re
import asyncio
import aiofiles
import os
import time

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
        await message.reply_text("🔒 Bot is locked!")
        return
    
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await message.reply_text(
            "⚠️ **Premium Required!**\n\n"
            "Contact owner for premium access.",
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
        "📚 **Select Platform:**\n\n"
        "Choose platform to extract batch links.",
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
        "📚 **Select Platform:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
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
        f"📱 **{app_name}**\n\n"
        f"🌐 {app_url}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**📖 How to Extract Links:**\n\n"
        f"**1. Login to Website**\n"
        f"   • Open {app_url}\n"
        f"   • Login with your credentials\n\n"
        f"**2. Open Developer Tools**\n"
        f"   • Press F12 key\n"
        f"   • Go to Network tab\n\n"
        f"**3. Play a Video**\n"
        f"   • Go to your batch\n"
        f"   • Click any video\n"
        f"   • Look for .m3u8 or .mp4 links\n\n"
        f"**4. Copy & Send Links**\n"
        f"   • Right-click link → Copy URL\n"
        f"   • Send here in format:\n\n"
        f"**Format:**\n"
        f"```\n"
        f"Video Title | https://domain.com/video.m3u8\n"
        f"```\n\n"
        f"**Example:**\n"
        f"```\n"
        f"Lecture 1 | https://appx-static.classx.co.in/video.m3u8\n"
        f"Lecture 2 | https://masterapi.tech/video2.m3u8\n"
        f"Notes PDF | https://domain.com/notes.pdf\n"
        f"```\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Send links (one per line or multiple)\n"
        f"Type `/done` when finished!\n\n"
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
        "❌ **Cancelled**\n\nUse /login to start again",
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
    
    if state == 'awaiting_batch_links':
        await handle_batch_links(client, message, data)

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
            f"📊 Total: {len(collected)}\n\n"
            f"Send more or type `/done`"
        )
    elif text.startswith('http'):
        title = f"Video {len(collected)+1}"
        collected.append(f"{title} | {text}")
        update_user_data(user_id, 'collected_links', collected)
        await message.reply_text(
            f"✅ **Added!**\n"
            f"📊 Total: {len(collected)}\n\n"
            f"Send more or `/done`"
        )
    else:
        await message.reply_text(
            "❌ **Invalid format!**\n\n"
            "Send: `Title | URL`\n"
            "Or just: `URL`\n\n"
            "Type `/done` when finished"
        )

@Client.on_message(filters.command("done"))
async def done_command(client: Client, message: Message):
    user_id = message.from_user.id
    session = get_user_state(user_id)
    
    if session.get('state') == 'awaiting_batch_links':
        data = session.get('data', {})
        await create_txt_file(client, message, user_id, data)
    else:
        await message.reply_text("❌ No active collection!\n\nUse /login")

async def create_txt_file(client, message, user_id, data):
    session = get_user_state(user_id)
    collected = session['data'].get('collected_links', [])
    
    if not collected:
        await message.reply_text("❌ No links collected!")
        return
    
    app_name = data.get('app_name', 'Platform')
    
    status = await message.reply_text("📝 Generating TXT...")
    
    video_count = sum(1 for l in collected if any(x in l.lower() for x in ['.m3u8', '.mp4', '.mkv']))
    pdf_count = sum(1 for l in collected if '.pdf' in l.lower())
    
    content = f"# {app_name} Batch\n"
    content += f"# Videos: {video_count} | PDFs: {pdf_count}\n"
    content += f"# Total: {len(collected)}\n\n"
    content += "\n".join(collected)
    
    os.makedirs("downloads", exist_ok=True)
    filename = f"downloads/batch_{user_id}_{int(time.time())}.txt"
    
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(content)
    
    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=(
            f"✅ **Batch TXT Generated!**\n\n"
            f"📚 Platform: {app_name}\n"
            f"🎥 Videos: {video_count}\n"
            f"📄 PDFs: {pdf_count}\n"
            f"📊 Total: {len(collected)}\n\n"
            f"**📥 Next Step:**\n"
            f"Send this file back to me!\n"
            f"I'll download all M3U8 videos!"
        )
    )
    
    await status.delete()
    clear_user_state(user_id)
    
    try:
        os.remove(filename)
    except:
        pass
