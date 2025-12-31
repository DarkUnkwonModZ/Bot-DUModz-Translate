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

# User Settings Store
user_pref = {} # {user_id: {'audio': False}}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CORE UTILS ---
async def check_membership(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_HANDLE, user_id=user_id)
        return member.status in [constants.ChatMemberStatus.MEMBER, constants.ChatMemberStatus.ADMINISTRATOR, constants.ChatMemberStatus.OWNER]
    except: return False

def get_clean_text(text, cmd):
    if text.startswith(cmd):
        return text[len(cmd):].strip()
    return text.strip()

# --- INTERFACE DESIGN ---

async def show_welcome_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, is_edit=False):
    """The Premium Dashboard after verification."""
    user = update.effective_user
    u_id = user.id
    audio_mode = "🔊 ENABLED" if user_pref.get(u_id, {}).get('audio', False) else "🔇 DISABLED"

    caption = (
        f"👑 **DARK UNKNOWN AI - DASHBOARD**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **USER:** {user.first_name}\n"
        f"🆔 **ID:** `{u_id}`\n"
        f"🛡️ **STATUS:** `PREMIUM VERIFIED` ✅\n"
        f"⚙️ **AUDIO MODE:** `{audio_mode}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ **How to use?**\n"
        f"➜ Just send any text to translate to English.\n"
        f"➜ Use `/bn <text>` for direct Bengali translation.\n\n"
        f"🚀 *Powered by Dark Unkwon ModZ*"
    )

    keyboard = [
        [InlineKeyboardButton("⚙️ SETTINGS", callback_data="open_settings"),
         InlineKeyboardButton("🌐 WEBSITE", url=WEBSITE_URL)],
        [InlineKeyboardButton("📢 OFFICIAL CHANNEL", url=CHANNEL_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_edit:
        await update.callback_query.edit_message_caption(caption=caption, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_photo(photo=LOGO_URL, caption=caption, reply_markup=reply_markup, parse_mode='Markdown')

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Verification Check
    if not await check_membership(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ VERIFY NOW", callback_data="verify_user")]
        ]
        await update.message.reply_photo(
            photo=LOGO_URL,
            caption=(
                "🛡️ **MEMBERSHIP VERIFICATION**\n\n"
                "You must join our official channel to use this premium AI tool.\n\n"
                f"📍 Channel: {CHANNEL_HANDLE}\n\n"
                "After joining, click the **Verify Now** button below."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    await show_welcome_dashboard(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_pref: user_pref[user_id] = {'audio': False}

    if query.data == "verify_user":
        if await check_membership(user_id, context.bot):
            # Smooth Transition Animation
            await query.edit_message_caption("⏳ **Verifying membership...**")
            await asyncio.sleep(1)
            await query.edit_message_caption("✅ **Access Granted! Loading Dashboard...**")
            await asyncio.sleep(1)
            await show_welcome_dashboard(update, context, is_edit=True)
        else:
            await context.bot.send_message(user_id, "⚠️ **Action Required:** Please join the channel first!")

    elif query.data == "open_settings":
        audio_btn = "🔊 AUDIO: ON" if user_pref[user_id]['audio'] else "🔇 AUDIO: OFF"
        keyboard = [
            [InlineKeyboardButton(audio_btn, callback_data="toggle_audio")],
            [InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_home")]
        ]
        await query.edit_message_caption("🛠️ **AI SETTINGS CONTROL**\nToggle features below:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == "toggle_audio":
        user_pref[user_id]['audio'] = not user_pref[user_id]['audio']
        await handle_callback(update, context) # Refresh menu

    elif query.data == "back_home":
        await show_welcome_dashboard(update, context, is_edit=True)

async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Re-check membership on every request for security
    if not await check_membership(user_id, context.bot):
        await update.message.reply_text("🚫 **Access Expired!** Please /start and verify again.")
        return

    raw_text = update.message.text
    if raw_text.startswith('/'): return

    # Animation
    status = await update.message.reply_text("⚡")
    await asyncio.sleep(0.3)
    await status.edit_text("⚙️ **AI is Processing...**")

    try:
        # Translation Logic
        translator = GoogleTranslator(source='auto', target='en')
        translated = translator.translate(raw_text)

        result = (
            f"💠 **AI TRANSLATION SUCCESS**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 **INPUT:** `{raw_text}`\n"
            f"📤 **ENGLISH:** `{translated}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Dark Unkwon AI Engine*"
        )
        
        await status.edit_text(result, parse_mode='Markdown')

        # Audio Logic
        if user_pref.get(user_id, {}).get('audio', False):
            tts = gTTS(text=translated, lang='en')
            voice_buf = io.BytesIO()
            tts.write_to_fp(voice_buf)
            voice_buf.seek(0)
            await update.message.reply_voice(voice=voice_buf, caption="🔊 Audio Transcription")

    except Exception as e:
        await status.edit_text(f"❌ **Error:** Translation failed. Try again later.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), translate_handler))
    
    print("Bot v5.0 Pro is Live!")
    app.run_polling()
