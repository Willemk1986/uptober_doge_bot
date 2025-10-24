import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from dotenv import load_dotenv, set_key
import secrets
import string
import base58
from cryptography.fernet import Fernet
import base64

from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

load_dotenv()

# Optional: Sentry
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[LoggingIntegration(level=logging.ERROR)],
        traces_sample_rate=1.0
    )
except ImportError:
    pass

from homescreen import start_handler, callback_handler
from setup_profile import get_profile_conversation_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

OWNER_ID = int(os.getenv('OWNER_ID', '0'))

# =============================================
# AUTO-SECURE WALLET SETUP
# =============================================
def setup_secure_wallet():
    env_path = '.env'
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(f"BOT_TOKEN={os.getenv('BOT_TOKEN', '')}\n")

    passphrase = os.getenv('SECURITY_PASSPHRASE')
    encrypted_seed = os.getenv('ENCRYPTED_BOT_WALLET_SEED')

    if not passphrase:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        passphrase = ''.join(secrets.choice(alphabet) for _ in range(40))
        set_key(env_path, "SECURITY_PASSPHRASE", passphrase)
        print(f"Generated secure passphrase: {passphrase[:8]}...")

    if not encrypted_seed:
        seed = secrets.token_bytes(32)
        pubkey = base58.b58encode(seed).decode()[:44]
        set_key(env_path, "PROJECT_WALLET_PUBKEY", pubkey)
        print(f"UPDOGE WALLET CREATED: {pubkey}")
        print(f"Send payments to: {pubkey}")

        key = base64.urlsafe_b64encode(passphrase.encode().ljust(32)[:32])
        f = Fernet(key)
        encrypted = f.encrypt(seed)
        encrypted_b58 = base58.b58encode(encrypted).decode()
        set_key(env_path, "ENCRYPTED_BOT_WALLET_SEED", encrypted_b58)
        print("Wallet seed encrypted and saved.")

    return passphrase

# =============================================
# BOT CORE
# =============================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update and hasattr(update, 'effective_chat'):
        await context.bot.send_message(update.effective_chat.id, "Doge tripped—tap /start to retry!")

async def restricted_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    if user_data.get('home_shown', False) and update.message.text and update.message.text.startswith('/'):
        if update.message.text in ['/start', '/help']:
            await update.message.reply_text("Use the buttons below!")
            return
    if user_data.get('awaiting_prompt'):
        from homescreen.image import handle_image_prompt
        await handle_image_prompt(update, context)
        return
    if any([update.message.photo, update.message.document, update.message.video, update.message.audio,
            update.message.sticker, update.message.voice, update.message.location,
            'http' in (update.message.text or ''), len(update.message.text or '') > 500]):
        try:
            await update.message.delete()
        except:
            pass
        await context.bot.send_message(update.effective_chat.id, "No media/links—text only for image prompts!")
        return
    if update.message.text and not update.message.text.startswith('/'):
        lang = user_data.get('language', 'en')
        await update.message.reply_text(f"{'Doge says' if lang == 'en' else 'Doge dice'}: {update.message.text}... Much wow!")

def main() -> None:
    setup_secure_wallet()

    token = os.getenv('BOT_TOKEN')
    if not token or token == 'your_telegram_bot_token_here':
        print("ERROR: Add BOT_TOKEN to .env")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(get_profile_conversation_handler())
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, restricted_message))

    application.add_error_handler(error_handler)

    with open('bot.pid', 'w') as f:
        f.write(str(os.getpid()))

    print("@UptoberDogeBot ready!")
    application.run_polling()

if __name__ == '__main__':
    main()