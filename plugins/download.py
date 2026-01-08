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

@Client.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    """Handle TXT file uploads"""
    user_id = message.from_user.id
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    # Check if it's a TXT file
    if not message.document.file_name.endswith('.txt'):
        return
    
    await process_txt_file(client, message)

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'login', 'setting', 'settings', 'lock', 'unlock', 'premium', 'rem', 'stats', 'ping', 'broadcast']))
async def handle_invalid_text(client: Client, message: Message):
    """Handle invalid commands"""
    user_id = message.from_user.id
    
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    await message.reply_text(
        "❌ **Invalid Command!**\n\n"
        "**Available Commands:**\n"
        "• `/start` - Start the bot\n"
        "• `/help` - Get detailed help\n"
        "• `/login` - Login to coaching app\n"
        "• `/setting` - Configure settings\n"
        "• `/ping` - Check bot speed\n\n"
        "**📝 Example Usage:**\n"
        "1. Use `/login` to select app\n"
        "2. Generate TXT file with batch links\n"
        "3. Send TXT file to download content\n\n"
        "Need help? Use `/help` command!"
    )

async def process_txt_file(client: Client, message: Message):
    """Process uploaded TXT file and download content"""
    user_id = message.from_user.id
    is_premium = await client.db.is_premium(user_id)
    
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
        return
    
    # Download and process TXT file
    status = await message.reply_text("📥 **Processing TXT file...**")
    
    try:
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
            return
        
        # Show summary
        await status.edit_text(
            f"📊 **Content Analysis**\n\n"
            f"🎥 **Videos:** {len(videos)}\n"
            f"📄 **PDFs:** {len(pdfs)}\n"
            f"📦 **Total Files:** {total_files}\n\n"
            f"⏳ **Starting download process...**"
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
                # Verify bot has access to channel
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
            pinned = await status.pin()
        except:
            pinned = None
        
        # Download counters
        success = 0
        failed = 0
        failed_files = []
        
        # Process videos
        for idx, video in enumerate(videos, 1):
            try:
                # Update status
                await status.edit_text(
                    f"🎥 **Downloading Videos**\n\n"
                    f"📊 Progress: `{idx}/{len(videos)}`\n"
                    f"📝 Current: `{video['title'][:50]}...`\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}"
                )
                
                # Simulate download (Replace with actual download logic)
                file_path = await download_file(video['url'], video['title'], status, "Downloading")
                
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
                    upload_msg = await status.edit_text(f"📤 **Uploading**\n\n`{video['title']}`")
                    
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
                    
                    # Increment downloads
                    await client.db.increment_downloads(user_id)
                    
                    # Sleep to avoid flood
                    if idx < len(videos):
                        await asyncio.sleep(Config.FLOOD_SLEEP)
                else:
                    failed += 1
                    failed_files.append(video['title'])
                    
            except Exception as e:
                failed += 1
                failed_files.append(video['title'])
                print(f"Error downloading {video['title']}: {e}")
                await asyncio.sleep(2)
        
        # Process PDFs
        for idx, pdf in enumerate(pdfs, 1):
            try:
                await status.edit_text(
                    f"📄 **Downloading PDFs**\n\n"
                    f"📊 Progress: `{idx}/{len(pdfs)}`\n"
                    f"📝 Current: `{pdf['title'][:50]}...`\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}"
                )
                
                # Download PDF
                file_path = await download_file(pdf['url'], pdf['title'], status, "Downloading")
                
                if file_path and os.path.exists(file_path):
                    caption = f"📄 **{pdf['title']}**\n\n"
                    caption += f"📊 **PDF {idx} of {len(pdfs)}**\n"
                    caption += f"✨ **Extracted by:** {credit}"
                    
                    upload_msg = await status.edit_text(f"📤 **Uploading PDF**\n\n`{pdf['title']}`")
                    
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
                    
                    if idx < len(pdfs):
                        await asyncio.sleep(Config.FLOOD_SLEEP)
                else:
                    failed += 1
                    failed_files.append(pdf['title'])
                    
            except Exception as e:
                failed += 1
                failed_files.append(pdf['title'])
                print(f"Error downloading {pdf['title']}: {e}")
                await asyncio.sleep(2)
        
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
            
            # Send to log channel in bot's topic
            await client.send_message(
                Config.LOG_CHANNEL,
                log_msg,
                message_thread_id=None  # Will create/use "Serena Lec" topic
            )
        except Exception as e:
            print(f"Failed to log: {e}")
        
    except Exception as e:
        await status.edit_text(f"❌ **Error:** `{str(e)}`\n\nPlease try again or contact support.")
        print(f"TXT Processing Error: {e}")

async def download_file(url, filename, status_msg, action="Downloading"):
    """
    Download file from URL with progress
    """
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
        
        # This is a simulation - Replace with actual download logic
        # For real implementation, use aiohttp to download from URL
        
        # Simulated download
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(Config.CHUNK_SIZE):
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
