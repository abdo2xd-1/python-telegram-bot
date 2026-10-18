import os
import threading
from dotenv import load_dotenv
from flask import Flask
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 8080))

# 1. إعداد سيرفر الويب لمنع السيرفر من النوم
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is alive and running 24/7!"

def run_web():
    server.run(host="0.0.0.0", port=PORT)

# 2. إعداد Gemini
ai_client = genai.Client(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """
أنت خبير تسويق إلكتروني وكتابة إعلانات بياعة (Direct-Response Copywriter) محترف في السوق المصري.
مهمتك:
عند استلام اسم منتج أو وصفه:
1. استنتج أهم 3 لـ 4 مميزات قوية للمنتج، وركز على "الفايدة الحقيقية" للمشتري مش بس المواصفات.
2. اكتب إعلاناً تسويقياً جذاباً باللهجة المصرية (عامية بيضاء تسويقية راقية وبياعة، بدون ابتذال).
3. هيكل الإعلان:
   - Hook خاطف في أول سطر يشد الانتباه ويلمس مشكلة أو رغبة عند العميل.
   - صلب الإعلان (Body): شرح مقنع للمميزات والفوائد بطريقة سلسة.
   - عرض حصري أو حافز للشراء (كمية محدودة، معاينة قبل الاستلام، شحن سريع).
   - دعوة صريحة ومباشرة لاتخاذ قرار (Call To Action - CTA).
4. اقترح 3 أفكار لعناوين/Hooks لفيديوهات Reels أو TikTok سريعة.
5. نسق النص بعلامات إيموجي وفواصل مريحة للقراءة.
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً بيك! 👋\n\n"
        "ابعتلي اسم أي منتج أو وصف بسيط ليه، وهحلل مميزاته وأكتبلك إعلان تسويقي بياع بالمصري فوراً 🚀"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("حصل ضغط على السيرفر، جرب تاني كمان لحظات.")
        print(f"Error: {e}")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        raise ValueError("تأكد من وضع TELEGRAM_BOT_TOKEN و GEMINI_API_KEY في ملف .env")

    # تشغيل السيرفر في خلفية منفصلة
    threading.Thread(target=run_web, daemon=True).start()

    # تشغيل البوت
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Server listening on port {PORT} and Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
