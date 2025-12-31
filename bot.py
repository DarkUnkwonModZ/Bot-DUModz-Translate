import os
import logging
import asyncio
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from deep_translator import GoogleTranslator
from gtts import gTTS

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8504263842
CHANNEL_HANDLE = "@DemoTestDUModz"
CHANNEL_URL = "https://t.me/DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

# User Data (Memory-based)
user_data = {} # {user_id: {'audio': False, 'verified': False}}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- UTILS ---
async def is_member(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_HANDLE, user_id=user_id)
        return member.status in [constants.ChatMemberStatus.MEMBER, constants.ChatMemberStatus.ADMINISTRATOR, constants.ChatMemberStatus.OWNER]
    except: return False

async def send_action_animation(message, text_list):
    """Creates a smooth loading animation effect."""
    for text in text_list:
        await message.edit_text(text, parse_mode='Markdown')
        await asyncio.sleep(0.5)

# --- CORE HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot
    
    # 1. PRE-VERIFICATION CHECK
    if not await is_member(user_id, bot):
        keyboard = [[InlineKeyboardButton("🔐 VERIFY MEMBERSHIP", url=CHANNEL_URL)],
                    [InlineKeyboardButton("🔄 CLICK TO CONFIRM", callback_data="verify_me")]]
        await update.message.reply_photo(
            photo=LOGO_URL,
            caption="⚠️ **ACCESS RESTRICTED**\n\nTo use this Premium Translator, you must join our official channel first.\n\nClick the buttons below to verify.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 2. POST-VERIFICATION WELCOME
    await show_dashboard(update, context)

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user = update.effective_user
    audio_status = "🔊 ON" if user_data.get(user.id, {}).get('audio', False) else "🔇 OFF"
    
    caption = (
        f"🌟 **WELCOME TO DARK UNKNOWN AI** 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **USER:** {user.first_name}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🛡️ **STATUS:** `PREMIUM VERIFIED` ✅\n"
        f"⚙️ **AUDIO:** `{audio_status}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 Send me any text to translate to **English**.\n"
        f"Use `/bn <text>` for Bengali specific mode."
    )
    
    keyboard = [
        [InlineKeyboardButton("⚙️ SETTINGS", callback_data="open_settings"),
         InlineKeyboardButton("🌐 WEBSITE", url=WEBSITE_URL)],
        [InlineKeyboardButton("📢 CHANNEL", url=CHANNEL_URL)]
    ]
    
    if edit:
        await update.callback_query.edit_message_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_photo(photo=LOGO_URL, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in user_data: user_data[user_id] = {'audio': False}
    
    # Toggle logic
    if query.data == "toggle_audio":
        user_data[user_id]['audio'] = not user_data[user_id]['audio']
        await query.answer("Audio Mode Updated!")
    
    audio_btn = "🔊 DISABLE AUDIO" if user_data[user_id]['audio'] else "🔇 ENABLE AUDIO"
    
    keyboard = [
        [InlineKeyboardButton(audio_btn, callback_data="toggle_audio")],
        [InlineKeyboardButton("🗑️ CLEAR CHAT", callback_data="clear_chat")],
        [InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_home")]
    ]
    
    await query.edit_message_caption(
        caption="🛠️ **PREMIUM SETTINGS CONTROL**\nCustomize your translation experience below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "verify_me":
        if await is_member(user_id, context.bot):
            await query.delete_message()
            await show_dashboard(update, context)
        else:
            await context.bot.send_message(user_id, "❌ Verification failed. Please join the channel first!")
            
    elif query.data == "open_settings" or query.data == "toggle_audio":
        await settings_menu(update, context)
        
    elif query.data == "back_home":
        await show_dashboard(update, context, edit=True)
        
    elif query.data == "clear_chat":
        await query.edit_message_caption("✨ Settings cleared and session refreshed!", 
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_home")]]))

async def translator_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Security Check
    if not await is_member(user_id, context.bot):
        await update.message.reply_text("🚫 Join @DemoTestDUModz to use this bot.")
        return

    text = update.message.text
    if text.startswith('/'): return # Ignore commands

    # Animation
    status = await update.message.reply_text("🔍")
    await send_action_animation(status, ["📡 Scanning...", "⚙️ Translating...", "✅ Done!"])

    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        
        result = (
            f"💠 **AI TRANSLATION**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📥 **INPUT:** `{text}`\n\n"
            f"📤 **ENGLISH:** `{translated}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Dark Unkwon AI*"
        )
        
        await status.edit_text(result, parse_mode='Markdown')

        # Audio Output
        if user_data.get(user_id, {}).get('audio', False):
            tts = gTTS(text=translated, lang='en')
            voice_io = io.BytesIO()
            tts.write_to_fp(voice_io)
            voice_io.seek(0)
            await update.message.reply_voice(voice=voice_io)

    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", settings_menu))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), translator_engine))
    
    print("Bot v4.0 is running perfectly...")
    app.run_polling()
