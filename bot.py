import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.error import BadRequest
from deep_translator import GoogleTranslator
from gtts import gTTS
import io

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8504263842
CHANNEL_HANDLE = "@DemoTestDUModz" # Your Channel Username
CHANNEL_URL = "https://t.me/DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

# Temporary Session Storage
user_settings = {} # {user_id: {'audio': False}}

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CORE FUNCTIONS ---

async def is_verified(user_id, bot):
    """Check if user is a member of the required channel."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_HANDLE, user_id=user_id)
        return member.status in [constants.ChatMemberStatus.MEMBER, 
                                 constants.ChatMemberStatus.ADMINISTRATOR, 
                                 constants.ChatMemberStatus.OWNER]
    except Exception:
        return False

def clean_payload(text, command):
    """Strips the command from text to ensure pure translation."""
    if text.startswith(command):
        return text[len(command):].strip()
    return text.strip()

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    verified = await is_verified(user.id, context.bot)
    
    status_emoji = "🟢 VERIFIED USER" if verified else "🔴 UNVERIFIED"
    audio_status = "🔊 ON" if user_settings.get(user.id, {}).get('audio', False) else "🔇 OFF"

    caption = (
        f"✨ **PREMIUM AI TRANSLATOR v3.0** ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **PROFILE INFO**\n"
        f"├ Name: {user.first_name}\n"
        f"├ User ID: `{user.id}`\n"
        f"└ Status: **{status_emoji}**\n\n"
        f"⚙️ **CURRENT CONFIG**\n"
        f"├ Mode: `Auto-Detection`\n"
        f"└ Audio Output: **{audio_status}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 *Powered by: Dark Unkwon ModZ*"
    )

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel to Verify", url=CHANNEL_URL)],
        [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_start")],
        [InlineKeyboardButton("🔊 Audio ON", callback_data="audio_on"),
         InlineKeyboardButton("🔇 Audio OFF", callback_data="audio_off")],
        [InlineKeyboardButton("🌐 Website", url=WEBSITE_URL),
         InlineKeyboardButton("👨‍💻 Admin", url="https://t.me/DarkUnkwon")]
    ]

    await update.message.reply_photo(
        photo=LOGO_URL,
        caption=caption,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_settings:
        user_settings[user_id] = {'audio': False}

    if query.data == "audio_on":
        user_settings[user_id]['audio'] = True
        await query.edit_message_caption(caption="✅ **Audio Mode Enabled!** Translations will now include voice messages.", parse_mode='Markdown', reply_markup=query.message.reply_markup)
    elif query.data == "audio_off":
        user_settings[user_id]['audio'] = False
        await query.edit_message_caption(caption="❌ **Audio Mode Disabled!** Only text will be sent.", parse_mode='Markdown', reply_markup=query.message.reply_markup)
    elif query.data == "refresh_start":
        # Simply re-run the start logic
        verified = await is_verified(user_id, context.bot)
        if verified:
            await query.edit_message_caption(caption="✅ **Verification Successful!** You can now use all features.", parse_mode='Markdown')
        else:
            await query.edit_message_caption(caption="⚠️ **Still Unverified!** Please join the channel first.", parse_mode='Markdown', reply_markup=query.message.reply_markup)

async def translate_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 1. Verification Security Check
    if not await is_verified(user_id, context.bot):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Click Here to Join", url=CHANNEL_URL)]])
        await update.message.reply_text(f"🚫 **Access Denied!**\n\nYou must join **{CHANNEL_HANDLE}** to use the translator.", reply_markup=btn)
        return

    # 2. Logic to filter commands
    raw_text = update.message.text
    if raw_text.startswith('/bn'):
        input_text = clean_payload(raw_text, '/bn')
        src_lang = 'bn'
    else:
        input_text = clean_payload(raw_text, '') # General text
        src_lang = 'auto'

    if not input_text:
        return # Do nothing if text is empty

    # 3. Translation Process
    wait_msg = await update.message.reply_text("⚡ *Processing translation...*", parse_mode='Markdown')
    
    try:
        translator = GoogleTranslator(source=src_lang, target='en')
        translated_text = translator.translate(input_text)

        response = (
            f"💠 **AI TRANSLATION**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 **INPUT ({src_lang.upper()}):**\n`{input_text}`\n\n"
            f"📤 **OUTPUT (EN):**\n`{translated_text}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Dark Unkwon ModZ AI Tool*"
        )

        await wait_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)

        # 4. Handle Audio Output (Advanced TTS)
        if user_settings.get(user_id, {}).get('audio', False):
            tts = gTTS(text=translated_text, lang='en')
            voice_bytes = io.BytesIO()
            tts.write_to_fp(voice_bytes)
            voice_bytes.seek(0)
            await update.message.reply_voice(voice=voice_bytes, caption="🔊 Voice Transcription")

    except Exception as e:
        await wait_msg.edit_text(f"❌ **Error:** `{str(e)}`", parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bn", translate_engine))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), translate_engine))
    
    print("Dark Unkwon Premium Bot is running...")
    app.run_polling()
