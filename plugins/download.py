from pyrogram import Client, filters
from pyrogram.types import Message
from utils.progress import progress_for_pyrogram
from utils.helpers import clean_filename, generate_thumbnail
from config import Config
import asyncio
import os
import time
import random

@Client.on_message(filters.document | filters.text)
async def handle_download(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        return
    
    # Check if it's a TXT file
    if message.document and message.document.file_name.endswith('.txt'):
        await process_txt_file(client, message)
    elif message.text and not message.text.startswith('/'):
        # Handle invalid commands
        await message.reply_text(
            "❌ **Invalid Command!**\n\n"
            "**Available Commands:**\n"
            "• /start - Start the bot\n"
            "• /help - Get help\n"
            "• /login - Login to coaching app\n"
            "• /settings - Configure settings\n\n"
            "**Example:** Send a TXT file to download content."
        )

async def process_txt_file(client: Client, message: Message):
    user_id = message.from_user.id
    is_premium = await client.db.is_premium(user_id)
    
    # Check if free user can generate txt
    if not is_premium:
        await message.reply_text(
            "⚠️ **Free users cannot download from TXT files!**\n\n"
            "Upgrade to premium for unlimited access.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Owner", url=f"tg://user?id={Config.OWNERS[0]}")]
            ])
        )
        return
    
    # Download TXT file
    status = await message.reply_text("📥 **Processing TXT file...**")
    
    try:
        file_path = await message.download()
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        os.remove(file_path)
        
        # Parse file (assuming format: Title | URL)
        videos = []
        pdfs = []
        
        for line in lines:
            line = line.strip()
            if '|' in line:
                title, url = line.split('|', 1)
                if any(ext in url.lower() for ext in ['.mp4', '.mkv', '.avi']):
                    videos.append({'title': title.strip(), 'url': url.strip()})
                elif '.pdf' in url.lower():
                    pdfs.append({'title': title.strip(), 'url': url.strip()})
        
        total_files = len(videos) + len(pdfs)
        
        if total_files == 0:
            await status.edit_text("❌ **No valid links found in TXT file!**")
            return
        
        await status.edit_text(
            f"📊 **Found:**\n"
            f"🎥 Videos: {len(videos)}\n"
            f"📄 PDFs: {len(pdfs)}\n\n"
            f"⏳ Starting download..."
        )
        
        # Get user settings
        settings = await client.db.get_user_settings(user_id)
        credit = settings.get('credit', 'Serena')
        channel_id = settings.get('channel_id') or message.chat.id
        thumbnail_mode = settings.get('thumbnail_mode', 'random')
        
        # Pin initial message
        try:
            await status.pin()
        except:
            pass
        
        # Download files
        success = 0
        failed = 0
        
        for idx, video in enumerate(videos, 1):
            try:
                # Simulate download (replace with actual download logic)
                await asyncio.sleep(2)  # Simulate download time
                
                # Check downloads limit for free users
                if not is_premium:
                    downloads_today = await client.db.get_downloads_today(user_id)
                    if downloads_today >= Config.FREE_LIMIT:
                        await message.reply_text(
                            f"⚠️ **Daily limit reached!**\n\n"
                            f"Free users: {Config.FREE_LIMIT} videos/day\n"
                            f"Upgrade to premium for unlimited downloads."
                        )
                        break
                
                # Generate caption
                caption = f"🎥 **{video['title']}**\n\n"
                caption += f"📊 Progress: {idx}/{len(videos)}\n"
                caption += f"✨ Extracted by: {credit}"
                
                # Send video (simulate - replace with actual file sending)
                # For now, just send info
                await client.send_message(
                    channel_id,
                    caption,
                    reply_to_message_id=message.id if channel_id == message.chat.id else None
                )
                
                await client.db.increment_downloads(user_id)
                success += 1
                
                # Delay between downloads
                if idx < len(videos):
                    await asyncio.sleep(Config.DOWNLOAD_DELAY)
                
            except Exception as e:
                failed += 1
                print(f"Error downloading {video['title']}: {e}")
        
        # Download PDFs
        for idx, pdf in enumerate(pdfs, 1):
            try:
                caption = f"📄 **{pdf['title']}**\n\n"
                caption += f"📊 Progress: {idx}/{len(pdfs)}\n"
                caption += f"✨ Extracted by: {credit}"
                
                await client.send_message(
                    channel_id,
                    caption,
                    reply_to_message_id=message.id if channel_id == message.chat.id else None
                )
                
                success += 1
                await asyncio.sleep(Config.DOWNLOAD_DELAY)
                
            except Exception as e:
                failed += 1
        
        # Final report
        await status.edit_text(
            f"✅ **Download Complete!**\n\n"
            f"📊 **Statistics:**\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"🎥 Videos: {len(videos)}\n"
            f"📄 PDFs: {len(pdfs)}\n\n"
            f"✨ All files sent!"
        )
        
        # Log to channel
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"#DOWNLOAD_COMPLETE\n\n"
                f"👤 User: {message.from_user.mention}\n"
                f"🆔 ID: `{user_id}`\n"
                f"📊 Success: {success}\n"
                f"❌ Failed: {failed}\n"
                f"📅 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except:
            pass
        
    except Exception as e:
        await status.edit_text(f"❌ **Error:** {str(e)}")
