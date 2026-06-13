import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Setup SkillLens Environment
load_dotenv()
from app.db.database import SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.services.chat_service import get_ai_response

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Welcome to SkillLensBot!\n\n"
        "I'm your official SkillLens Career Coach on Telegram.\n\n"
        "To get started, please link your SkillLens account by typing:\n"
        "`/login your_email@example.com`"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/login <email>`", parse_mode='Markdown')
        return
    
    email = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            await update.message.reply_text(f"❌ User with email {email} not found in SkillLens database.")
            return
        
        # Check if already linked to someone else
        existing = db.query(User).filter(User.telegram_id == chat_id).first()
        if existing and existing.email != email:
             # Unlink old
             existing.telegram_id = None
        
        # Link current user
        user.telegram_id = chat_id
        db.commit()
        
        await update.message.reply_text(
            f"✅ Account linked successfully!\n"
            f"Hi {user.full_name}, I'm ready to help you with your career.\n\n"
            "You can now ask me anything, like:\n"
            "- 'Review my resume'\n"
            "- 'Give me interview tips'\n"
            "- 'Analyze a job description'"
        )
    finally:
        db.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    content = update.message.text
    if not content: return

    # Show "Typing..." action
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    user_context = ""
    model_hint = None
    
    db = SessionLocal()
    try:
        # Find linked user via Telegram ID
        user = db.query(User).filter(User.telegram_id == chat_id).first()
        if user:
            model_hint = user.ai_model
            # Get latest resume for context
            resume = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.updated_at.desc()).first()
            if resume and resume.content:
                user_context = f"\n[User's Current Resume Preview]:\n{resume.content[:2500]}\n"
        else:
            user_context = "\n(System: User is not yet logged in / linked. Advise them to use /login if they want personalized help.)\n"
    finally:
        db.close()

    # Build prompt for AI
    messages = [
        {"role": "user", "content": f"{content}\n{user_context}"}
    ]

    try:
        reply = get_ai_response(messages, model_hint=model_hint)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"AI response failed: {e}")
        await update.message.reply_text("⚠️ Disconnected from AI brain. Please try again later.")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
        exit(1)
        
    token = token.strip()
    
    # Building application with better timeouts for unstable connections
    application = (ApplicationBuilder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build())
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('login', login))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("SkillLens Career Coach Bot is starting (FULL AI VERSION)...")
    application.run_polling()
