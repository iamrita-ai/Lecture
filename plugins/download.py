from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.progress import progress_for_pyrogram
from utils.helpers import clean_filename, generate_thumbnail
from utils.universal_downloader import download_any_file
from config import Config
import asyncio
import os
import time
import random
import aiofiles
import re

# Store active tasks
active_tasks = {}

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_task(client: Client, message: Message):
    """Cancel ongoing download task"""
    user_id = message.from_user.id
    
    if user_id in active_tasks:
        active_tasks[user_id]['cancelled'] = True
        await message.reply_text(
            "🛑 **Cancelling...**\n\n"
            "⏳ Stopping downloads...\n"
            "🗑️ Cleaning up files..."
        )
    else:
        await message.reply_text("❌ **No active task!**")

@Client.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    """Handle TXT file uploads"""
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    if user_id in active_tasks and not active_tasks[user_id].get('cancelled'):
        await message.reply_text("⚠️ **Task running!** Use /cancel first")
        return
    
    if not message.document.file_name.endswith('.txt'):
        return
    
    await process_txt_file(client, message)

async def process_txt_file(client: Client, message: Message):
    """Process TXT file"""
    user_id = message.from_user.id
    is_premium = await client.db.is_premium(user_id)
    
    active_tasks[user_id] = {'cancelled': False, 'status': 'starting'}
    
    try:
        if not is_premium:
            await message.reply_text(
                "⚠️ **Premium Required!**\n\n"
                "TXT downloads need premium.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
                ])
            )
            del active_tasks[user_id]
            return
        
        status = await message.reply_text("📥 **Processing TXT...**")
        
        file_path = await message.download()
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            lines = content.strip().split('\n')
        
        try:
            os.remove(file_path)
        except:
            pass
        
        if active_tasks[user_id]['cancelled']:
            await status.edit_text("🛑 **Cancelled!**")
            del active_tasks[user_id]
            return
        
        files = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            title = None
            url = None
            
            if '|' in line:
                parts = line.split('|', 1)
                title = parts[0].strip()
                url = parts[1].strip()
            elif line.startswith('http'):
                url = line
                title = f"File {len(files)+1}"
            
            if url:
                files.append({'title': title, 'url': url})
        
        if not files:
            await status.edit_text("❌ **No valid links!**")
            del active_tasks[user_id]
            return
        
        await status.edit_text(
            f"📊 **Found {len(files)} files**\n\n"
            f"⏳ Starting downloads...\n\n"
            f"💡 /cancel to stop"
        )
        
        await asyncio.sleep(2)
        
        settings = await client.db.get_user_settings(user_id)
        credit = settings.get('credit', 'Serena')
        channel_id = settings.get('channel_id')
        thumbnail_mode = settings.get('thumbnail_mode', 'random')
        
        if channel_id:
            try:
                await client.get_chat(channel_id)
                target_chat = channel_id
                reply_to = None
            except:
                target_chat = message.chat.id
                reply_to = message.id
        else:
            target_chat = message.chat.id
            reply_to = message.id
        
        is_topic = False
        topic_id = None
        if target_chat == message.chat.id and hasattr(message, 'message_thread_id'):
            is_topic = True
            topic_id = message.message_thread_id
        
        try:
            await status.pin()
        except:
            pass
        
        active_tasks[user_id]['status'] = 'downloading'
        
        success = 0
        failed = 0
        failed_files = []
        
        for idx, file_data in enumerate(files, 1):
            if active_tasks[user_id]['cancelled']:
                await status.edit_text(
                    f"🛑 **Cancelled!**\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}"
                )
                break
            
            try:
                await status.edit_text(
                    f"📥 **Downloading**\n\n"
                    f"📊 {idx}/{len(files)}\n"
                    f"📝 `{file_data['title'][:50]}...`\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}\n\n"
                    f"💡 /cancel to stop"
                )
                
                file_path = await download_any_file(
                    file_data['url'],
                    file_data['title'],
                    status,
                    user_id
                )
                
                if active_tasks[user_id]['cancelled']:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass
                    break
                
                if file_path and os.path.exists(file_path):
                    caption = f"📁 **{file_data['title']}**\n\n"
                    caption += f"📊 File {idx} of {len(files)}\n"
                    caption += f"✨ Extracted by: {credit}"
                    
                    file_ext = file_path.split('.')[-1].lower()
                    
                    upload_msg = await status.edit_text(
                        f"📤 **Uploading**\n\n`{file_data['title']}`"
                    )
                    
                    if file_ext in ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm']:
                        thumb = None
                        if thumbnail_mode == 'random' and random.randint(1, 3) == 1:
                            thumb = await generate_thumbnail()
                        
                        await client.send_video(
                            chat_id=target_chat,
                            video=file_path,
                            caption=caption,
                            thumb=thumb,
                            supports_streaming=True,
                            reply_to_message_id=reply_to if not is_topic else None,
                            message_thread_id=topic_id if is_topic else None,
                            progress=progress_for_pyrogram,
                            progress_args=("Uploading", upload_msg, time.time(), file_data['title'])
                        )
                        
                        if thumb:
                            try:
                                os.remove(thumb)
                            except:
                                pass
                    
                    elif file_ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']:
                        await client.send_audio(
                            chat_id=target_chat,
                            audio=file_path,
                            caption=caption,
                            reply_to_message_id=reply_to if not is_topic else None,
                            message_thread_id=topic_id if is_topic else None,
                            progress=progress_for_pyrogram,
                            progress_args=("Uploading", upload_msg, time.time(), file_data['title'])
                        )
                    
                    else:
                        await client.send_document(
                            chat_id=target_chat,
                            document=file_path,
                            caption=caption,
                            reply_to_message_id=reply_to if not is_topic else None,
                            message_thread_id=topic_id if is_topic else None,
                            progress=progress_for_pyrogram,
                            progress_args=("Uploading", upload_msg, time.time(), file_data['title'])
                        )
                    
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    
                    success += 1
                    await client.db.increment_downloads(user_id)
                    
                    if idx < len(files) and not active_tasks[user_id]['cancelled']:
                        await asyncio.sleep(Config.FLOOD_SLEEP)
                else:
                    failed += 1
                    failed_files.append(file_data['title'])
                    
            except Exception as e:
                failed += 1
                failed_files.append(file_data['title'])
                print(f"Error: {e}")
                await asyncio.sleep(2)
        
        if active_tasks[user_id]['cancelled']:
            cleanup_downloads()
            await status.unpin()
            del active_tasks[user_id]
            return
        
        report = f"✅ **Complete!**\n\n"
        report += f"✅ Success: `{success}`\n"
        report += f"❌ Failed: `{failed}`\n"
        report += f"📦 Total: `{len(files)}`\n\n"
        
        if failed_files:
            report += f"**⚠️ Failed:**\n"
            for fail in failed_files[:5]:
                report += f"• `{fail[:40]}...`\n"
        
        await status.edit_text(report)
        
        try:
            await status.unpin()
        except:
            pass
        
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"#BATCH\n\n"
                f"👤 {message.from_user.mention}\n"
                f"✅ {success} | ❌ {failed}"
            )
        except:
            pass
        
        cleanup_downloads()
        
    except Exception as e:
        await message.reply_text(f"❌ Error: `{str(e)}`")
    
    finally:
        if user_id in active_tasks:
            del active_tasks[user_id]

def cleanup_downloads():
    try:
        if os.path.exists("downloads"):
            for file in os.listdir("downloads"):
                file_path = os.path.join("downloads", file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except:
                    pass
    except:
        pass

# ====== DIRECT LINK DOWNLOAD ======

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast', 'cancel', 'done']), group=2)
async def handle_direct_link(client: Client, message: Message):
    """Handle direct URLs"""
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    from utils.session import get_user_state
    session = get_user_state(user_id)
    
    if session.get('state'):
        return
    
    url_pattern = re.compile(r'http[s]?://[^\s]+')
    
    if url_pattern.match(message.text.strip()):
        await download_single_file(client, message)
        return
    
    await message.reply_text(
        "❌ **Invalid!**\n\n"
        "Send:\n"
        "• Direct URL\n"
        "• TXT file\n\n"
        "/help for commands"
    )

async def download_single_file(client: Client, message: Message):
    """Download single file"""
    user_id = message.from_user.id
    is_premium = await client.db.is_premium(user_id)
    
    if not is_premium:
        downloads_today = await client.db.get_downloads_today(user_id)
        if downloads_today >= Config.FREE_LIMIT:
            await message.reply_text(
                f"⚠️ Limit: {Config.FREE_LIMIT}/day\n"
                f"Used: {downloads_today}\n\n"
                f"Get premium!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Premium", url="https://t.me/technicalserena")]
                ])
            )
            return
    
    url = message.text.strip()
    
    try:
        filename = url.split('/')[-1].split('?')[0]
        if not filename or '.' not in filename:
            filename = "download"
    except:
        filename = "download"
    
    status = await message.reply_text(
        f"📥 **Downloading...**\n\n"
        f"`{filename[:50]}...`\n\n"
        f"⏳ Please wait..."
    )
    
    try:
        file_path = await download_any_file(url, filename, status, user_id)
        
        if not file_path or not os.path.exists(file_path):
            await status.edit_text("❌ **Failed!**")
            return
        
        settings = await client.db.get_user_settings(user_id)
        credit = settings.get('credit', 'Serena')
        
        caption = f"📁 **{filename}**\n\n✨ By: {credit}"
        
        await status.edit_text(f"📤 **Uploading...**\n\n`{filename}`")
        
        file_ext = file_path.split('.')[-1].lower()
        
        if file_ext in ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm']:
            thumb = await generate_thumbnail()
            
            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=caption,
                thumb=thumb,
                supports_streaming=True,
                reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=("Uploading", status, time.time(), filename)
            )
            
            if thumb:
                try:
                    os.remove(thumb)
                except:
                    pass
        
        elif file_ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=caption,
                reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=("Uploading", status, time.time(), filename)
            )
        
        else:
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=caption,
                reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=("Uploading", status, time.time(), filename)
            )
        
        try:
            os.remove(file_path)
        except:
            pass
        
        await status.edit_text(f"✅ **Done!**\n\n`{filename}`")
        
        await client.db.increment_downloads(user_id)
        
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"#DIRECT\n\n"
                f"👤 {message.from_user.mention}\n"
                f"📁 {filename}"
            )
        except:
            pass
        
    except Exception as e:
        await status.edit_text(f"❌ Error: `{str(e)[:100]}`")
