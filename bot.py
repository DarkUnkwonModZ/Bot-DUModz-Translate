import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import BadRequest
from deep_translator import GoogleTranslator
from gtts import gTTS

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8504263842
ADMIN_USERNAME = "@DarkUnkwon"
CHANNEL_USERNAME = "@DemoTestDUModz"
CHANNEL_URL = "https://t.me/DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

# Temporary User Settings (Note: Resets on GitHub Action Restart)
user_audio_mode = {} 

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- HELPER FUNCTIONS ---

async def check_verify(user_id, bot):
    """Checks if the user is verified (joined the channel)."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in [constants.ChatMemberStatus.MEMBER, constants.ChatMemberStatus.ADMINISTRATOR, constants.ChatMemberStatus.OWNER]:
            return "✅ Verified (Premium Access)"
        return "❌ Unverified (Access Restricted)"
    except Exception:
        return "❌ Unverified (Access Restricted)"

def clean_text(text, command_to_remove=None):
    if command_to_remove and text.startswith(command_to_remove):
        return text[len(command_to_remove):].strip()
    return text.strip()

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    v_status = await check_verify(user.id, context.bot)
    
    # Audio Mode Status
    audio_status = "🔊 ON" if user_audio_mode.get(user.id, False) else "🔇 OFF (Default)"
    
    welcome_msg = (
        f"👑 **DARK UNKNOWN MODZ - PREMIUM AI**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User Profile:**\n"
        f"├ Name: {user.first_name}\n"
        f"├ ID: `{user.id}`\n"
        f"└ Status: **{v_status}**\n\n"
        f"⚙️ **Bot Settings:**\n"
        f"├ Translation: `Auto -> English`\n"
        f"└ Audio Mode: **{audio_status}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 *Join our channel to unlock all features!*"
    )

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("🔊 Audio Mode ON", callback_data="audio_on"),
         InlineKeyboardButton("🔇 Audio Mode OFF", callback_data="audio_off")],
        [InlineKeyboardButton("🌐 Website", url=WEBSITE_URL),
         InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
    ]
    
    await update.message.reply_photo(
        photo=LOGO_URL,
        caption=welcome_msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def toggle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "audio_on":
        user_audio_mode[user_id] = True
        await query.edit_message_caption(caption="✅ **Audio Mode Enabled!** You will receive voice messages.", parse_mode='Markdown')
    else:
        user_audio_mode[user_id] = False
        await query.edit_message_caption(caption="❌ **Audio Mode Disabled!** Text only output.", parse_mode='Markdown')

async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot
    
    # 1. Verification Check
    v_status = await check_verify(user_id, bot)
    if "❌" in v_status:
        await update.message.reply_text(f"⚠️ **Access Denied!**\n\nPlease join {CHANNEL_USERNAME} and type /start again.")
        return

    # 2. Extract Text
    raw_text = update.message.text
    if raw_text.startswith('/bn'):
        mode_label = "🇧🇩 Bengali ➔ 🇺🇸 English"
        input_text = clean_text(raw_text, '/bn')
        src = 'bn'
    else:
        mode_label = "🌍 Auto Detect ➔ 🇺🇸 English"
        input_text = clean_text(raw_text)
        src = 'auto'

    if not input_text:
        await update.message.reply_text("❗ **Error:** Please provide text to translate.")
        return

    # 3. Process
    status_msg = await update.message.reply_text("🔄 **AI is translating...**")
    
    try:
        translated = GoogleTranslator(source=src, target='en').translate(input_text)
        
        response = (
            f"✨ **TRANSLATION SUCCESS** ✨\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 **Mode:** `{mode_label}`\n"
            f"📥 **Input:** `{input_text}`\n"
            f"📤 **Output:** `{translated}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *By: {ADMIN_USERNAME}*"
        )
        
        await status_msg.edit_text(response, parse_mode='Markdown')

        # 4. Audio Feature
        if user_audio_mode.get(user_id, False):
            voice_file = f"voice_{user_id}.mp3"
            tts = gTTS(text=translated, lang='en')
            tts.save(voice_file)
            await update.message.reply_voice(voice=open(voice_file, 'rb'), caption="🔊 Voice Output")
            os.remove(voice_file) # Clean up

    except Exception as e:
        await status_msg.edit_text(f"❌ **API Error:** {str(e)}")

if __name__ == '__main__':
    if not TOKEN:
        print("Set BOT_TOKEN in Environment Variables!")
    else:
        from telegram.ext import CallbackQueryHandler
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("bn", handle_translation))
        app.add_handler(CallbackQueryHandler(toggle_audio))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_translation))
        
        print("Ultimate Advanced Bot is Online...")
        app.run_polling()
