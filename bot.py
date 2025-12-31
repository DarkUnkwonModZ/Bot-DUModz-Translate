import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from deep_translator import GoogleTranslator

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Configuration & Links
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"
TELEGRAM_LINK = "https://t.me/DarkUnkwonModZ"
WEBSITE_LINK = "https://darkunkwonmodz.blogspot.com"
BRAND_NAME = "Dark Unkwon ModZ"

# Translation Functions
def translate_text(text, target_lang='en', source_lang='auto'):
    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        return translated
    except Exception as e:
        return f"Error: {str(e)}"

# Welcome Screen (Start Command)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👋 **স্বাগতম, {user_name}!**\n\n"
        f"🚀 **{BRAND_NAME}** অ্যাডভান্সড ট্রান্সলেটর বটে আপনাকে স্বাগতম।\n\n"
        "✨ **ফিচারসমূহ:**\n"
        "🔹 **Auto Detect:** যেকোনো ভাষা দিলে সরাসরি English হবে।\n"
        "🔹 **BN to EN:** নির্দিষ্টভাবে বাংলা থেকে ইংলিশ করতে পারবেন।\n"
        "🔹 **Commands:** দ্রুত কাজের জন্য কমান্ড ব্যবহার করুন।\n\n"
        "নিচের বাটনগুলো ব্যবহার করে আমাদের সাথে যুক্ত থাকুন।"
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_LINK)],
        [InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=LOGO_URL,
        caption=welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **কিভাবে ব্যবহার করবেন?**\n\n"
        "1️⃣ শুধু যেকোনো টেক্সট লিখুন, আমি অটো-ডিটেক্ট করে English করে দেব।\n"
        "2️⃣ `/bn` লিখে স্পেস দিয়ে বাংলা লিখলে সেটি English হবে।\n"
        "3️⃣ `/auto` লিখে যেকোনো ভাষা দিলে সেটি English হবে।\n\n"
        "⚡ Powered by Dark Unkwon ModZ"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Auto Detect to English Handler
async def handle_auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text:
        wait_msg = await update.message.reply_text("⏳ Detecting and Translating...")
        translated = translate_text(user_text, target_lang='en', source_lang='auto')
        
        response = (
            f"✅ **Translated to English:**\n\n"
            f"📝 `{translated}`\n\n"
            f"👤 *Powered by {BRAND_NAME}*"
        )
        await wait_msg.edit_text(response, parse_mode='Markdown')

# Specific BN to EN Command Handler
async def bn_to_en_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ দয়া করে কমান্ডের সাথে টেক্সট দিন। উদাহরণ: `/bn কেমন আছো`")
        return
    
    user_text = " ".join(context.args)
    translated = translate_text(user_text, target_lang='en', source_lang='bn')
    await update.message.reply_text(f"🇧🇩 ➡️ 🇺🇸 **English:**\n\n`{translated}`", parse_mode='Markdown')

if __name__ == '__main__':
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("Error: BOT_TOKEN not found!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("bn", bn_to_en_command))
        app.add_handler(CommandHandler("auto", handle_auto_translate))
        
        # General messages will be handled as auto-detect
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_auto_translate))
        
        print("Advanced Bot is running...")
        app.run_polling()
