from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.progress import progress_for_pyrogram, progress_bar
from utils.helpers import clean_filename, generate_thumbnail
from config import Config
import asyncio
import os
import time
import random
import aiohttp
import aiofiles

# Store active tasks
active_tasks = {}

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_task(client: Client, message: Message):
    """Cancel ongoing download task"""
    user_id = message.from_user.id
    
    if user_id in active_tasks:
        task_info = active_tasks[user_id]
        task_info['cancelled'] = True
        
        await message.reply_text(
            "🛑 **Task Cancellation Requested!**\n\n"
            "⏳ Stopping current download...\n"
            "🗑️ Cleaning up files...\n\n"
            "Please wait a moment."
        )
    else:
        await message.reply_text(
            "❌ **No Active Task!**\n\n"
            "You don't have any ongoing download task.\n\n"
            "Use /login to start downloading."
        )

@Client.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    """Handle TXT file uploads"""
    user_id = message.from_user.id
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    # Check if user already has active task
    if user_id in active_tasks and not active_tasks[user_id].get('cancelled'):
        await message.reply_text(
            "⚠️ **Task Already Running!**\n\n"
            "You already have an active download task.\n\n"
            "Use /cancel to stop it first."
        )
        return
    
    # Check if it's a TXT file
    if not message.document.file_name.endswith('.txt'):
        return
    
    await process_txt_file(client, message)

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast', 'cancel']))
async def handle_invalid_text(client: Client, message: Message):
    """Handle invalid commands"""
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    # First check if user is in a session (login flow)
    from utils.session import get_user_state
    session = get_user_state(user_id)
    
    if session.get('state'):
        # User is in login flow, don't handle here
        # Let login.py handle it
        return
    
    # Check if it's a valid URL for single download
    import re
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    if url_pattern.match(message.text):
        # It's a URL, try to download
        await handle_single_download(client, message)
        return
    
    # Invalid command
    await message.reply_text(
        "❌ **Invalid Input!**\n\n"
        "**Available Commands:**\n"
        "• `/start` - Start the bot\n"
        "• `/help` - Get help\n"
        "• `/login` - Login to platform\n"
        "• `/setting` - Settings\n"
        "• `/cancel` - Cancel task\n\n"
        "**Or send:**\n"
        "• Direct video/PDF link to download\n"
        "• TXT file with batch links"
    )

async def process_txt_file(client: Client, message: Message):
    """Process uploaded TXT file and download content"""
    user_id = message.from_user.id
    is_premium = await client.db.is_premium(user_id)
    
    # Initialize task tracking
    active_tasks[user_id] = {
        'cancelled': False,
        'status': 'starting'
    }
    
    try:
        # Check if free user can download from txt
        if not is_premium:
            await message.reply_text(
                "⚠️ **Premium Feature!**\n\n"
                "Free users cannot download from TXT files.\n\n"
                "**Free User Limits:**\n"
                "• 10 direct downloads per day\n"
                "• No batch downloads\n"
                "• No TXT file processing\n\n"
                "**💎 Premium Benefits:**\n"
                "• Unlimited downloads\n"
                "• Batch downloads via TXT\n"
                "• Priority support\n"
                "• Custom settings\n\n"
                "Contact owner for premium access!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Contact Owner", url=f"tg://user?id={Config.OWNERS[0]}")]
                ])
            )
            del active_tasks[user_id]
            return
        
        # Download and process TXT file
        status = await message.reply_text("📥 **Processing TXT file...**")
        
        # Download file
        file_path = await message.download()
        
        # Read file content
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            lines = content.strip().split('\n')
        
        # Delete downloaded txt file
        try:
            os.remove(file_path)
        except:
            pass
        
        # Check if cancelled
        if active_tasks[user_id]['cancelled']:
            await status.edit_text("🛑 **Task Cancelled!**")
            del active_tasks[user_id]
            return
        
        # Parse file (Format: Title | URL)
        videos = []
        pdfs = []
        
        for line in lines:
            line = line.strip()
            if not line or '|' not in line:
                continue
            
            try:
                title, url = line.split('|', 1)
                title = title.strip()
                url = url.strip()
                
                # Categorize by extension
                if any(ext in url.lower() for ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv']):
                    videos.append({'title': title, 'url': url})
                elif '.pdf' in url.lower():
                    pdfs.append({'title': title, 'url': url})
            except:
                continue
        
        total_files = len(videos) + len(pdfs)
        
        if total_files == 0:
            await status.edit_text(
                "❌ **No Valid Links Found!**\n\n"
                "**TXT File Format:**\n"
                "`Video Title | https://video-link.mp4`\n"
                "`PDF Title | https://pdf-link.pdf`\n\n"
                "Each link on a new line."
            )
            del active_tasks[user_id]
            return
        
        # Show summary
        await status.edit_text(
            f"📊 **Content Analysis**\n\n"
            f"🎥 **Videos:** {len(videos)}\n"
            f"📄 **PDFs:** {len(pdfs)}\n"
            f"📦 **Total Files:** {total_files}\n\n"
            f"⏳ **Starting download process...**\n\n"
            f"💡 Use /cancel to stop this task"
        )
        
        await asyncio.sleep(2)
        
        # Get user settings
        settings = await client.db.get_user_settings(user_id)
        credit = settings.get('credit', 'Serena')
        channel_id = settings.get('channel_id')
        thumbnail_mode = settings.get('thumbnail_mode', 'random')
        
        # Determine where to send files
        if channel_id:
            try:
                await client.get_chat(channel_id)
                target_chat = channel_id
                reply_to = None
            except:
                await status.edit_text("❌ **Invalid channel ID in settings!** Sending to DM instead...")
                await asyncio.sleep(2)
                target_chat = message.chat.id
                reply_to = message.id
        else:
            target_chat = message.chat.id
            reply_to = message.id
        
        # Check if group has topics
        is_topic = False
        topic_id = None
        if target_chat == message.chat.id and hasattr(message, 'message_thread_id'):
            is_topic = True
            topic_id = message.message_thread_id
        
        # Pin starting message
        try:
            await status.pin()
        except:
            pass
        
        # Update task status
        active_tasks[user_id]['status'] = 'downloading'
        
        # Download counters
        success = 0
        failed = 0
        failed_files = []
        
        # Process videos
        for idx, video in enumerate(videos, 1):
            # Check if cancelled
            if active_tasks[user_id]['cancelled']:
                await status.edit_text(
                    f"🛑 **Task Cancelled by User!**\n\n"
                    f"📊 **Progress Before Cancellation:**\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}\n"
                    f"⏸️ Stopped at: {idx}/{len(videos)} videos\n\n"
                    f"🗑️ Cleaning up..."
                )
                break
            
            try:
                # Update status
                await status.edit_text(
                    f"🎥 **Downloading Videos**\n\n"
                    f"📊 Progress: `{idx}/{len(videos)}`\n"
                    f"📝 Current: `{video['title'][:50]}...`\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}\n\n"
                    f"💡 Use /cancel to stop"
                )
                
                # Download file
                file_path = await download_file(
                    video['url'], 
                    video['title'], 
                    status, 
                    "Downloading",
                    user_id
                )
                
                # Check if cancelled during download
                if active_tasks[user_id]['cancelled']:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass
                    break
                
                if file_path and os.path.exists(file_path):
                    # Generate caption
                    caption = f"🎥 **{video['title']}**\n\n"
                    caption += f"📊 **Video {idx} of {len(videos)}**\n"
                    caption += f"✨ **Extracted by:** {credit}"
                    
                    # Generate thumbnail (1/3 random)
                    thumb = None
                    if thumbnail_mode == 'random':
                        if random.randint(1, 3) == 1:
                            thumb = await generate_thumbnail()
                    
                    # Upload video
                    upload_msg = await status.edit_text(
                        f"📤 **Uploading**\n\n`{video['title']}`\n\n"
                        f"💡 Use /cancel to stop"
                    )
                    
                    sent_msg = await client.send_video(
                        chat_id=target_chat,
                        video=file_path,
                        caption=caption,
                        thumb=thumb,
                        reply_to_message_id=reply_to if not is_topic else None,
                        message_thread_id=topic_id if is_topic else None,
                        progress=progress_for_pyrogram,
                        progress_args=(upload_msg, time.time(), video['title'])
                    )
                    
                    # Clean up
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    
                    if thumb:
                        try:
                            os.remove(thumb)
                        except:
                            pass
                    
                    success += 1
                    await client.db.increment_downloads(user_id)
                    
                    # Sleep to avoid flood
                    if idx < len(videos) and not active_tasks[user_id]['cancelled']:
                        await asyncio.sleep(Config.FLOOD_SLEEP)
                else:
                    failed += 1
                    failed_files.append(video['title'])
                    
            except Exception as e:
                failed += 1
                failed_files.append(video['title'])
                print(f"Error downloading {video['title']}: {e}")
                await asyncio.sleep(2)
        
        # Check if cancelled
        if active_tasks[user_id]['cancelled']:
            # Cleanup
            cleanup_downloads()
            await status.unpin()
            del active_tasks[user_id]
            return
        
        # Process PDFs
        for idx, pdf in enumerate(pdfs, 1):
            # Check if cancelled
            if active_tasks[user_id]['cancelled']:
                await status.edit_text(
                    f"🛑 **Task Cancelled by User!**\n\n"
                    f"📊 **Final Stats:**\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}\n\n"
                    f"🗑️ Cleaning up..."
                )
                break
            
            try:
                await status.edit_text(
                    f"📄 **Downloading PDFs**\n\n"
                    f"📊 Progress: `{idx}/{len(pdfs)}`\n"
                    f"📝 Current: `{pdf['title'][:50]}...`\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}\n\n"
                    f"💡 Use /cancel to stop"
                )
                
                # Download PDF
                file_path = await download_file(
                    pdf['url'], 
                    pdf['title'], 
                    status, 
                    "Downloading",
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
                    caption = f"📄 **{pdf['title']}**\n\n"
                    caption += f"📊 **PDF {idx} of {len(pdfs)}**\n"
                    caption += f"✨ **Extracted by:** {credit}"
                    
                    upload_msg = await status.edit_text(
                        f"📤 **Uploading PDF**\n\n`{pdf['title']}`\n\n"
                        f"💡 Use /cancel to stop"
                    )
                    
                    await client.send_document(
                        chat_id=target_chat,
                        document=file_path,
                        caption=caption,
                        reply_to_message_id=reply_to if not is_topic else None,
                        message_thread_id=topic_id if is_topic else None,
                        progress=progress_for_pyrogram,
                        progress_args=(upload_msg, time.time(), pdf['title'])
                    )
                    
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    
                    success += 1
                    await client.db.increment_downloads(user_id)
                    
                    if idx < len(pdfs) and not active_tasks[user_id]['cancelled']:
                        await asyncio.sleep(Config.FLOOD_SLEEP)
                else:
                    failed += 1
                    failed_files.append(pdf['title'])
                    
            except Exception as e:
                failed += 1
                failed_files.append(pdf['title'])
                print(f"Error downloading {pdf['title']}: {e}")
                await asyncio.sleep(2)
        
        # Check if task was cancelled
        if active_tasks[user_id]['cancelled']:
            cleanup_downloads()
            await status.unpin()
            del active_tasks[user_id]
            return
        
        # Final report
        report = f"✅ **Download Complete!**\n\n"
        report += f"📊 **Statistics:**\n"
        report += f"✅ Success: `{success}`\n"
        report += f"❌ Failed: `{failed}`\n"
        report += f"🎥 Videos: `{len(videos)}`\n"
        report += f"📄 PDFs: `{len(pdfs)}`\n"
        report += f"📦 Total: `{total_files}`\n\n"
        
        if failed_files:
            report += f"**⚠️ Failed Files:**\n"
            for fail in failed_files[:5]:
                report += f"• `{fail[:40]}...`\n"
            if len(failed_files) > 5:
                report += f"• *...and {len(failed_files)-5} more*\n"
        
        report += f"\n✨ **All files sent successfully!**"
        
        await status.edit_text(report)
        
        # Unpin status message
        try:
            await status.unpin()
        except:
            pass
        
        # Log to channel
        try:
            log_msg = f"#DOWNLOAD_COMPLETE\n\n"
            log_msg += f"👤 **User:** {message.from_user.mention}\n"
            log_msg += f"🆔 **ID:** `{user_id}`\n"
            log_msg += f"📝 **Username:** @{message.from_user.username or 'None'}\n\n"
            log_msg += f"📊 **Stats:**\n"
            log_msg += f"✅ Success: {success}\n"
            log_msg += f"❌ Failed: {failed}\n"
            log_msg += f"🎥 Videos: {len(videos)}\n"
            log_msg += f"📄 PDFs: {len(pdfs)}\n\n"
            log_msg += f"📅 **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            await client.send_message(
                Config.LOG_CHANNEL,
                log_msg
            )
        except Exception as e:
            print(f"Failed to log: {e}")
        
        # Cleanup
        cleanup_downloads()
        
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`\n\nPlease try again or contact support.")
        print(f"TXT Processing Error: {e}")
    
    finally:
        # Remove from active tasks
        if user_id in active_tasks:
            del active_tasks[user_id]

async def download_file(url, filename, status_msg, action="Downloading", user_id=None):
    """Download file from URL with progress and cancellation support"""
    try:
        clean_name = clean_filename(filename)
        
        # Determine extension
        if not any(clean_name.endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.pdf', '.mov']):
            if '.pdf' in url.lower():
                clean_name += '.pdf'
            else:
                clean_name += '.mp4'
        
        file_path = f"downloads/{clean_name}"
        
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        
        # Download with aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
                if resp.status == 200:
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(Config.CHUNK_SIZE):
                            # Check if cancelled
                            if user_id and user_id in active_tasks and active_tasks[user_id]['cancelled']:
                                return None
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            await progress_for_pyrogram(
                                downloaded, 
                                total_size, 
                                action, 
                                status_msg, 
                                start_time, 
                                filename
                            )
                    
                    return file_path
                else:
                    return None
                    
    except Exception as e:
        print(f"Download error for {filename}: {e}")
        return None

def cleanup_downloads():
    """Clean up downloads directory"""
    try:
        if os.path.exists("downloads"):
            for file in os.listdir("downloads"):
                file_path = os.path.join("downloads", file)
                try:
                    os.remove(file_path)
                except:
                    pass
    except:
        pass

async def download_single_file(client: Client, message: Message):
    """Download single file from direct URL"""
    user_id = message.from_user.id
    is_premium = await client.db.is_premium(user_id)
    
    # Check free user limit
    if not is_premium:
        downloads_today = await client.db.get_downloads_today(user_id)
        if downloads_today >= Config.FREE_LIMIT:
            await message.reply_text(
                f"⚠️ **Daily Limit Reached!**\n\n"
                f"Free users: {Config.FREE_LIMIT} downloads/day\n"
                f"You've used: {downloads_today}/{Config.FREE_LIMIT}\n\n"
                f"Upgrade to premium for unlimited downloads!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Get Premium", url=f"tg://user?id={Config.OWNERS[0]}")]
                ])
            )
            return
    
    url = message.text.strip()
    
    # Extract filename from URL
    try:
        filename = url.split('/')[-1].split('?')[0]
        if not filename:
            filename = "download"
        
        # Add extension if not present
        if '.' not in filename:
            if any(ext in url.lower() for ext in ['.mp4', '.mkv', '.avi']):
                filename += '.mp4'
            elif '.pdf' in url.lower():
                filename += '.pdf'
            else:
                filename += '.mp4'
    except:
        filename = "download.mp4"
    
    status = await message.reply_text(
        f"📥 **Downloading...**\n\n"
        f"📝 File: `{filename[:50]}...`\n\n"
        f"⏳ Please wait..."
    )
    
    try:
        # Download file
        file_path = await download_file(
            url,
            filename,
            status,
            "Downloading",
            user_id
        )
        
        if not file_path or not os.path.exists(file_path):
            await status.edit_text(
                "❌ **Download Failed!**\n\n"
                "Please check if the URL is valid and accessible."
            )
            return
        
        # Get user settings
        settings = await client.db.get_user_settings(user_id)
        credit = settings.get('credit', 'Serena')
        
        # Prepare caption
        caption = f"📁 **{filename}**\n\n"
        caption += f"✨ **Downloaded by:** {credit}"
        
        # Send file
        await status.edit_text(f"📤 **Uploading...**\n\n`{filename}`")
        
        if file_path.endswith('.pdf'):
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=caption,
                reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=(status, time.time(), filename)
            )
        else:
            # Generate thumbnail
            thumb = await generate_thumbnail()
            
            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=caption,
                thumb=thumb,
                reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=(status, time.time(), filename)
            )
            
            if thumb:
                try:
                    os.remove(thumb)
                except:
                    pass
        
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
        
        await status.edit_text(
            "✅ **Download Complete!**\n\n"
            f"📁 File: `{filename}`\n"
            f"✨ Sent successfully!"
        )
        
        # Increment download count
        await client.db.increment_downloads(user_id)
        
        # Log
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"#SINGLE_DOWNLOAD\n\n"
                f"👤 {message.from_user.mention}\n"
                f"🆔 `{user_id}`\n"
                f"📁 {filename}\n"
                f"🔗 {url[:50]}...\n"
                f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except:
            pass
        
    except Exception as e:
        await status.edit_text(
            f"❌ **Error!**\n\n"
            f"`{str(e)[:100]}`\n\n"
            f"Please try again or contact support."
        )
        print(f"Single download error: {e}")
