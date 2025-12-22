import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- 1. CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "8074588063:AAEDmnnUnFNGhVkdtOOQvy7ZbSamsJTGpnI" 

# --- OFFICIAL MEKONGSMS CREDENTIALS ---
# Note: postsms.aspx is for POST requests
API_URL = "https://sandbox.mekongsms.com/api/postsms.aspx"
API_USERNAME = "vireak_support1@apitest"
API_PASSWORD = "98dbd835838cd7dfe49193532c77deeb"
API_SENDER = "MKN UAT"
API_CD_VALUE = "Test001"
API_INT_VALUE = "1" 

# Conversation States
PHONE, SMS_CONTENT = range(2)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 **MekongSMS Bot (POST Mode)**\n\nPlease input the **Phone Number**:"
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    
    # Auto-fix: Ensure 855 prefix
    clean_phone = phone.replace("+", "").replace(" ", "")
    if clean_phone.startswith("0"):
        clean_phone = "855" + clean_phone[1:]
    elif not clean_phone.startswith("855"):
        clean_phone = "855" + clean_phone
        
    context.user_data["phone"] = clean_phone
    await update.message.reply_text(f"✅ Phone `{clean_phone}` saved. Now input the **Message**:")
    return SMS_CONTENT

async def send_sms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message_text = update.message.text
    phone_number = context.user_data.get("phone")

    await update.message.reply_text("⏳ Sending via POST...")

    # --- CRITICAL FIX: USE 'data' FOR POST REQUESTS ---
    payload = {
        "username": API_USERNAME,
        "pass": API_PASSWORD,
        "sender": API_SENDER,
        "smstext": message_text,
        "gsm": phone_number,
        "cd": API_CD_VALUE,
        "int": API_INT_VALUE
    }

    try:
        # 1. Use requests.post (not get)
        # 2. Use 'data=payload' (not params)
        response = requests.post(API_URL, data=payload, timeout=15)
        
        print(f"DEBUG Response: {response.text}")

        if response.status_code == 200:
            if "result=0" in response.text.lower():
                await update.message.reply_text(
                    f"✅ **SUCCESS**\n\n"
                    f"📲 To: `{phone_number}`\n"
                    f"📩 Msg: `{message_text}`\n"
                    f"📝 Response: `{response.text}`"
                )
            else:
                # If error 102 persists, the API might strictly require GET on a different URL
                # But for postsms.aspx, this POST method is correct.
                await update.message.reply_text(
                    f"⚠️ **API RETURN**\nOutput: `{response.text}`"
                )
        else:
            await update.message.reply_text(f"❌ HTTP ERROR: {response.status_code}")

    except Exception as e:
        await update.message.reply_text(f"❌ SYSTEM ERROR: {str(e)}")

    await update.message.reply_text("🔄 Type /start to try again.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 Cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SMS_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sms)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("Bot is running...")
    application.run_polling()