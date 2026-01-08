from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

# Indian Coaching Apps
COACHING_APPS = {
    "pw": {"name": "📚 Physics Wallah (PW)", "icon": "📚"},
    "unacademy": {"name": "🎓 Unacademy", "icon": "🎓"},
    "vedantu": {"name": "📖 Vedantu", "icon": "📖"},
    "byjus": {"name": "🔬 BYJU'S", "icon": "🔬"},
    "khan": {"name": "🌟 Khan Academy India", "icon": "🌟"},
    "toppr": {"name": "🎯 Toppr", "icon": "🎯"},
    "doubtnut": {"name": "❓ Doubtnut", "icon": "❓"},
    "embibe": {"name": "📊 Embibe", "icon": "📊"},
    "gradeup": {"name": "📈 Gradeup", "icon": "📈"},
    "testbook": {"name": "📝 Testbook", "icon": "📝"},
    "adda247": {"name": "💯 Adda247", "icon": "💯"},
    "oliveboard": {"name": "🎪 Oliveboard", "icon": "🎪"},
}

@Client.on_message(filters.command("login"))
async def login_command(client: Client, message):
    user_id = message.from_user.id
    
    # Check if bot is locked
    if await client.db.is_bot_locked() and user_id not in Config.OWNERS:
        await message.reply_text("🔒 **Bot is locked!** Contact owner.")
        return
    
    # Check premium or free limit
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await message.reply_text(
            "⚠️ **Free users cannot use login feature!**\n\n"
            "Contact owner for premium access.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Owner", url=f"tg://user?id={Config.OWNERS[0]}")]
            ])
        )
        return
    
    # Show coaching apps
    buttons = []
    row = []
    for app_id, app_data in COACHING_APPS.items():
        row.append(InlineKeyboardButton(app_data["icon"] + " " + app_data["name"].split(" (")[0], callback_data=f"app_{app_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="start")])
    
    await message.reply_text(
        "📚 **Select Your Coaching App:**\n\n"
        "Choose the app you want to login to:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^login_menu$"))
async def login_menu_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    
    # Check premium
    is_premium = await client.db.is_premium(user_id)
    if not is_premium:
        await query.answer("⚠️ Premium required!", show_alert=True)
        return
    
    # Show coaching apps
    buttons = []
    row = []
    for app_id, app_data in COACHING_APPS.items():
        row.append(InlineKeyboardButton(app_data["icon"] + " " + app_data["name"].split(" (")[0], callback_data=f"app_{app_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="start")])
    
    await query.message.edit_text(
        "📚 **Select Your Coaching App:**\n\n"
        "Choose the app you want to login to:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^app_"))
async def app_selected_callback(client: Client, query: CallbackQuery):
    app_id = query.data.split("_")[1]
    app_name = COACHING_APPS[app_id]["name"]
    
    await query.message.edit_text(
        f"📱 **{app_name}**\n\n"
        f"📞 **Please send your phone number:**\n\n"
        f"Example: `+919876543210` or `9876543210`\n\n"
        f"⚠️ Country code is optional for Indian numbers.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="login_menu")]
        ])
    )
    
    # Store app selection in user session (you'll need to implement session storage)
    await query.answer(f"Selected: {app_name}")

# Note: Actual login implementation would require:
# 1. Session storage for user state
# 2. Phone number validation
# 3. OTP verification
# 4. API integration with coaching platforms
# This is a template - actual implementation depends on specific APIs
