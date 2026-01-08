from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
import time
import psutil
import asyncio

def is_owner(user_id):
    return user_id in Config.OWNERS

@Client.on_message(filters.command("lock") & filters.user(Config.OWNERS))
async def lock_command(client: Client, message: Message):
    await client.db.lock_bot()
    await message.reply_text(
        "🔒 **Bot Locked!**\n\nOnly owners can use now.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
        ])
    )

@Client.on_message(filters.command("unlock") & filters.user(Config.OWNERS))
async def unlock_command(client: Client, message: Message):
    await client.db.unlock_bot()
    await message.reply_text(
        "🔓 **Bot Unlocked!**\n\nEveryone can use now.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
        ])
    )

@Client.on_message(filters.command("premium") & filters.user(Config.OWNERS))
async def premium_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/premium <user_id>`")
        return
    
    try:
        user_id = int(message.command[1])
        await client.db.add_premium(user_id)
        await message.reply_text(f"✅ **Premium added to user:** `{user_id}`")
        
        try:
            await client.send_message(
                user_id,
                "🎉 **Congratulations!**\n\n"
                "You have been granted **Premium Access**!\n\n"
                "✨ **Premium Benefits:**\n"
                "• Unlimited downloads\n"
                "• Priority support\n"
                "• Access to all features\n\n"
                "Enjoy! 🚀",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
                ])
            )
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ **Invalid user ID!**")

@Client.on_message(filters.command("rem") & filters.user(Config.OWNERS))
async def remove_premium_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/rem <user_id>`")
        return
    
    try:
        user_id = int(message.command[1])
        await client.db.remove_premium(user_id)
        await message.reply_text(f"✅ **Premium removed from user:** `{user_id}`")
        
        try:
            await client.send_message(
                user_id,
                "⚠️ **Premium Access Removed**\n\n"
                "Your premium access has been revoked.\n"
                "Contact owner for more details.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena")]
                ])
            )
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ **Invalid user ID!**")

@Client.on_message(filters.command("stats") & filters.user(Config.OWNERS))
async def stats_command(client: Client, message: Message):
    stats = await client.db.get_bot_stats()
    is_locked = await client.db.is_bot_locked()
    
    # System stats
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    text = f"📊 **Bot Statistics**\n\n"
    text += f"**Bot Status:**\n"
    text += f"🔐 Lock: {'🔒 Locked' if is_locked else '🔓 Unlocked'}\n"
    text += f"⚡ CPU: {cpu}%\n"
    text += f"💾 RAM: {ram}%\n"
    text += f"💿 Disk: {disk}%\n\n"
    text += f"**User Statistics:**\n"
    text += f"👥 Total Users: {stats['total_users']}\n"
    text += f"💎 Premium Users: {stats['premium_users']}\n"
    text += f"🟢 Active Today: {stats['active_today']}\n\n"
    text += f"📅 **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    buttons = [
        [InlineKeyboardButton("👤 Owner", url="https://t.me/technicalserena"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/serenaunzipbot")]
    ]
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNERS))
async def broadcast_command(client: Client, message: Message):
    if message.reply_to_message:
        msg = await message.reply_text("📢 **Broadcasting...**")
        users = await client.db.users.find({}).to_list(length=None)
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await message.reply_to_message.copy(user['user_id'])
                success += 1
            except:
                failed += 1
            
            await asyncio.sleep(0.1)
        
        await msg.edit_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}"
        )
    else:
        await message.reply_text("Reply to a message to broadcast!")
