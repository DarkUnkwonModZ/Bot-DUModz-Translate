import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from deep_translator import GoogleTranslator

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Translate Function
def translate_bn_to_en(text):
    try:
        translated = GoogleTranslator(source='bn', target='en').translate(text)
        return translated
    except Exception as e:
        return f"Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হাই বন্ধু! আমি বাংলা থেকে ইংলিশ অনুবাদক বট। আমাকে যেকোনো বাংলা টেক্সট পাঠাও।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text:
        translated_text = translate_bn_to_en(user_text)
        await update.message.reply_text(f"English: {translated_text}")

if __name__ == '__main__':
    # Get token from environment variable
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("Error: BOT_TOKEN not found!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Bot is running...")
        app.run_polling()
