import os
import logging
import asyncio
import io
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from deep_translator import GoogleTranslator
from gtts import gTTS

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = 8504263842
LOG_CHANNEL = "@dumodzbotmanager" # লগ চ্যানেল
CHANNEL_HANDLE = "@DemoTestDUModz"
CHANNEL_URL = "https://t.me/DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

# User Settings & Stats Store (Note: Resets on restart)
user_pref = {} 
total_users = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CORE UTILS ---

async def check_membership(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_HANDLE, user_id=user_id)
        return member.status in [constants.ChatMemberStatus.MEMBER, constants.ChatMemberStatus.ADMINISTRATOR, constants.ChatMemberStatus.OWNER]
    except Exception:
        return False

def get_user_data(user_id):
    if user_id not in user_pref:
        user_pref[user_id] = {'audio': False, 'mode': 'en'}
    return user_pref[user_id]

async def send_log(context, update: Update, action_type="Activity"):
    """চ্যানেলে লগ পাঠানোর সিস্টেম"""
    user = update.effective_user
    log_text = (
        f"🔔 **NEW BOT LOG**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** {user.first_name}\n"
        f"🔤 **Username:** @{user.username if user.username else 'N/A'}\n"
        f"🗣 **Language:** {user.language_code}\n"
        f"🆔 **Chat ID:** `{user.id}`\n"
        f"📝 **Action:** {action_type}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=log_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Log Error: {e}")

# --- AUTO RESTART LOGIC ---
async def auto_restart_timer(context: ContextTypes.DEFAULT_TYPE):
    """৪ ঘণ্টা পর পর বট রিস্টার্ট করবে"""
    try:
        msg = "🔄 **System Auto-Restarting (4-Hour Cycle)...**"
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=msg, parse_mode='Markdown')
        print("Restarting bot...")
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        print(f"Restart Error: {e}")

# --- TRANSLATION ENGINE ---
async def process_translation(update: Update, context: ContextTypes.DEFAULT_TYPE, target_lang, text):
    user_id = update.effective_user.id
    status = await update.message.reply_text("⚡ **AI Processing...**")
    
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        
        lang_name = target_lang.upper()
        result = (
            f"🚀 **DARK UNKNOWN AI RESULT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 **INPUT:** `{text}`\n"
            f"📤 **{lang_name}:** `{translated}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ *Powered by Dark Unkwon ModZ*"
        )
        
        await status.edit_text(result, parse_mode='Markdown')

        u_data = get_user_data(user_id)
        if u_data['audio']:
            tts = gTTS(text=translated, lang=target_lang)
            voice_buf = io.BytesIO()
            tts.write_to_fp(voice_buf)
            voice_buf.seek(0)
            await update.message.reply_voice(voice=voice_buf, caption=f"🔊 {lang_name} Audio Pronunciation")

    except Exception as e:
        await status.edit_text(f"❌ **Error:** {str(e)}")

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    total_users.add(user.id)
    
    # লগ পাঠানো
    await send_log(context, update, "Started the Bot")

    if not await check_membership(user.id, context.bot):
        keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_URL)],
                    [InlineKeyboardButton("✅ VERIFY NOW", callback_data="verify_user")]]
        await update.message.reply_photo(photo=LOGO_URL, caption="🛡️ **MEMBERSHIP REQUIRED**\n\nPlease join our channel to use this AI.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await show_dashboard(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **DARK UNKNOWN AI - HELP MENU**\n\n"
        "✨ **Basic Usage:**\n"
        "Just send any text, it will auto-translate to **English**.\n\n"
        "⚡ **Commands:**\n"
        "➜ `/bn`, `/en`, `/hi`, `/ar`, `/fr`, `/es` <text>\n\n"
        "👑 **Admin Only:**\n"
        "➜ `/stats` - Check user count\n"
        "➜ `/broadcast` - Message to all users"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# --- ADMIN COMMANDS ---
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(f"📊 **Bot Stats**\n\n👥 Total Users Since Last Restart: {len(total_users)}", parse_mode='Markdown')

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Use: `/broadcast Your Message`")
        return
    
    broadcast_msg = " ".join(context.args)
    count = 0
    for uid in list(total_users):
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **ADMIN MESSAGE**\n\n{broadcast_msg}", parse_mode='Markdown')
            count += 1
        except: continue
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

# --- INTERFACE ---

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, is_edit=False):
    user = update.effective_user
    u_data = get_user_data(user.id)
    audio_status = "🔊 ON" if u_data['audio'] else "🔇 OFF"
    
    caption = (
        f"👑 **WELCOME TO PREMIUM AI**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **USER:** {user.first_name}\n"
        f"🛡️ **STATUS:** `VERIFIED` ✅\n"
        f"⚙️ **AUDIO MODE:** `{audio_status}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Tip: Use /help to see all commands.*"
    )
    keyboard = [
        [InlineKeyboardButton(f"SETTINGS: {audio_status}", callback_data="toggle_audio")],
        [InlineKeyboardButton("🌐 WEBSITE", url=WEBSITE_URL), InlineKeyboardButton("📢 CHANNEL", url=CHANNEL_URL)]
    ]
    
    if is_edit:
        await update.callback_query.edit_message_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_photo(photo=LOGO_URL, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "verify_user":
        if await check_membership(user_id, context.bot):
            await query.edit_message_caption("✅ Verified! Loading...")
            await show_dashboard(update, context, is_edit=True)
        else:
            await context.bot.answer_callback_query(query.id, "⚠️ Join the channel first!", show_alert=True)

    elif query.data == "toggle_audio":
        u_data = get_user_data(user_id)
        u_data['audio'] = not u_data['audio']
        await show_dashboard(update, context, is_edit=True)

# --- MESSAGES ---

async def direct_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update.effective_user.id, context.bot): return
    cmd = update.message.text.split()[0][1:].lower()
    text = " ".join(update.message.text.split()[1:])
    
    if not text:
        await update.message.reply_text(f"❌ Usage: `/{cmd} Hello`")
        return
        
    lang_map = {'bn': 'bn', 'en': 'en', 'hi': 'hi', 'ar': 'ar', 'fr': 'fr', 'es': 'es'}
    if cmd in lang_map:
        await process_translation(update, context, lang_map[cmd], text)

async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update.effective_user.id, context.bot): return
    if update.message.text.startswith('/'): return
    await process_translation(update, context, 'en', update.message.text)

# --- MAIN RUNNER ---
if __name__ == '__main__':
    if not TOKEN:
        print("BOT_TOKEN missing!")
        exit(1)

    # ApplicationBuilder build
    app = ApplicationBuilder().token(TOKEN).build()
    
    # 4-Hour Auto Restart Job
    if app.job_queue:
        app.job_queue.run_once(auto_restart_timer, 14400) # 14400s = 4 Hours
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler(["bn", "en", "hi", "ar", "fr", "es"], direct_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_translate))
    
    print("🚀 Dark Unknown AI Bot v6.0 Fixed is running...")
    app.run_polling()
