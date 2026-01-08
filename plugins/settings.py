from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

@Client.on_message(filters.command("setting") | filters.command("settings"))
async def settings_command(client: Client, message):
    user_id = message.from_user.id
    settings = await client.db.get_user_settings(user_id)
    
    channel = settings.get('channel_id', 'Not Set')
    credit = settings.get('credit', 'Serena')
    thumbnail = settings.get('thumbnail_mode', 'Random')
    
    text = f"⚙️ **Your Settings**\n\n"
    text += f"📢 Channel ID: `{channel}`\n"
    text += f"✨ Credit: `{credit}`\n"
    text += f"🖼️ Thumbnail: `{thumbnail.title()}`"
    
    buttons = [
        [InlineKeyboardButton("📢 Set Channel ID", callback_data="set_channel")],
        [InlineKeyboardButton("✨ Add Credit", callback_data="set_credit")],
        [InlineKeyboardButton("🖼️ Thumbnail Mode", callback_data="set_thumbnail")],
        [InlineKeyboardButton("🔄 Reset Settings", callback_data="reset_settings")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ]
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^settings$"))
async def settings_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    settings = await client.db.get_user_settings(user_id)
    
    channel = settings.get('channel_id', 'Not Set')
    credit = settings.get('credit', 'Serena')
    thumbnail = settings.get('thumbnail_mode', 'Random')
    
    text = f"⚙️ **Your Settings**\n\n"
    text += f"📢 Channel ID: `{channel}`\n"
    text += f"✨ Credit: `{credit}`\n"
    text += f"🖼️ Thumbnail: `{thumbnail.title()}`"
    
    buttons = [
        [InlineKeyboardButton("📢 Set Channel ID", callback_data="set_channel")],
        [InlineKeyboardButton("✨ Add Credit", callback_data="set_credit")],
        [InlineKeyboardButton("🖼️ Thumbnail Mode", callback_data="set_thumbnail")],
        [InlineKeyboardButton("🔄 Reset Settings", callback_data="reset_settings")],
        [InlineKeyboardButton("🏠 Home", callback_data="start")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_thumbnail$"))
async def thumbnail_callback(client: Client, query: CallbackQuery):
    buttons = [
        [InlineKeyboardButton("🎲 Random Thumbnail", callback_data="thumb_random")],
        [InlineKeyboardButton("📦 Batch Thumbnail", callback_data="thumb_batch")],
        [InlineKeyboardButton("◀️ Back", callback_data="settings")]
    ]
    
    await query.message.edit_text(
        "🖼️ **Select Thumbnail Mode:**\n\n"
        "• **Random:** Random thumbnails on 1/3 videos\n"
        "• **Batch:** Use batch thumbnail for all videos",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^thumb_"))
async def set_thumb_callback(client: Client, query: CallbackQuery):
    mode = query.data.split("_")[1]
    await client.db.update_settings(query.from_user.id, "thumbnail_mode", mode)
    await query.answer(f"✅ Thumbnail mode set to {mode.title()}!", show_alert=True)
    await settings_callback(client, query)

@Client.on_callback_query(filters.regex("^reset_settings$"))
async def reset_callback(client: Client, query: CallbackQuery):
    await client.db.reset_settings(query.from_user.id)
    await query.answer("✅ Settings reset successfully!", show_alert=True)
    await settings_callback(client, query)

@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client: Client, query: CallbackQuery):
    await query.message.delete()
