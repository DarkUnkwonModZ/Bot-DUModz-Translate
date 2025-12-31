import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import BadRequest
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8504263842
ADMIN_USERNAME = "@DarkUnkwon"
CHANNEL_USERNAME = "@DemoTestDUModz"  # For Force Join
CHANNEL_URL = "https://t.me/DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- HELPER FUNCTIONS ---

async def is_subscribed(user_id, bot):
    """Checks if the user is a member of the required channel."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in [constants.ChatMemberStatus.MEMBER, 
                                 constants.ChatMemberStatus.ADMINISTRATOR, 
                                 constants.ChatMemberStatus.OWNER]
    except BadRequest:
        return False
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return True # Default to true to avoid blocking users if bot isn't admin

def clean_text(text, command_to_remove=None):
    """Removes commands from text so they don't get translated."""
    if command_to_remove and text.startswith(command_to_remove):
        return text[len(command_to_remove):].strip()
    return text.strip()

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Notify Admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"🚀 **New User Started Bot!**\n\n👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 User: @{user.username}",
            parse_mode='Markdown'
        )
    except:
        pass

    welcome_msg = (
        f"🌟 **PREMIUM TRANSLATOR PRO** 🌟\n\n"
        f"Welcome, **{user.first_name}**!\n"
        f"I am an Advanced AI Translator powered by **Dark Unkwon ModZ**.\n\n"
        "✨ **Capabilities:**\n"
        "🔹 Auto Detect any language ➔ English\n"
        "🔹 Specific Bengali ➔ English via `/bn` command\n"
        "🔹 High-Speed & Precise Translation\n\n"
        "📢 **Note:** You must join our channel to use this service."
    )

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("🌐 Official Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👨‍💻 Admin Support", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
    ]
    
    await update.message.reply_photo(
        photo=LOGO_URL,
        caption=welcome_msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot
    
    # 1. Force Join Security Check
    if not await is_subscribed(user_id, bot):
        join_btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Join Now", url=CHANNEL_URL)]])
        await update.message.reply_text(
            f"❌ **Access Denied!**\n\nYou must join our official channel **{CHANNEL_USERNAME}** to use this bot.",
            reply_markup=join_btn
        )
        return

    # 2. Process Text
    raw_text = update.message.text
    
    # Determine source language and clean command text
    if raw_text.startswith('/bn'):
        source_lang = 'bn'
        target_lang = 'en'
        input_text = clean_text(raw_text, '/bn')
    else:
        source_lang = 'auto'
        target_lang = 'en'
        input_text = clean_text(raw_text)

    if not input_text:
        await update.message.reply_text("❗ Please provide text after the command.")
        return

    # 3. Translation Process
    status_msg = await update.message.reply_text("🔍 *AI is processing text...*", parse_mode='Markdown')
    
    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(input_text)
        
        response = (
            f"💠 **Translation Result** 💠\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📥 **Input:** `{input_text}`\n\n"
            f"📤 **English:** `{translated}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Powered by:** [Dark Unkwon ModZ]({WEBSITE_URL})"
        )
        
        await status_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)
    
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** Translation failed. Try again later.")
        logging.error(f"Translation Error: {e}")

if __name__ == '__main__':
    if not TOKEN:
        print("BOT_TOKEN is missing in Environment Variables!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("bn", handle_translation))
        
        # General messages handle auto-detect
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_translation))
        
        print("Premium Bot is Online...")
        app.run_polling()
