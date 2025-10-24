import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import get_text

logger = logging.getLogger("homescreen")

# Logo path
LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'updoge.jpg')

# CA
CA = "AiChxGThnvFWGGGzA6rejb3nzPbm1eZKrq42BzWQpump"
CA_LINK = "https://dexscreener.com/solana/aichxgthnvfwgggza6rejb3nzpbm1ezkrq42bzwqpump"

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — show centered logo + CA + buttons."""
    user_data = context.user_data
    user_data['home_shown'] = True
    user_data.setdefault('language', 'en')

    message = update.message or update.callback_query.message

    # Welcome + CA
    welcome = (
        f"*{get_text(user_data, 'welcome_title')}*\n\n"
        f"{get_text(user_data, 'welcome_body', user=update.effective_user.mention_html())}\n\n"
        f"{get_text(user_data, 'welcome_tip')}\n\n"
        f"{get_text(user_data, 'ca_text', ca=CA, link=CA_LINK)}"
    )

    # Send logo + caption
    try:
        with open(LOGO_PATH, 'rb') as photo:
            await message.reply_photo(
                photo=photo,
                caption=welcome,
                parse_mode='Markdown',
                reply_markup=home_keyboard(user_data)
            )
    except FileNotFoundError:
        logger.warning("updoge.jpg missing")
        await message.reply_text(welcome, parse_mode='Markdown', reply_markup=home_keyboard(user_data))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button taps."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # Prevent edit error on photo messages
    if query.message.photo:
        await query.message.delete()
        await start_handler(update, context)
        return

    if data == "lang_menu":
        from .about import handle_language_button
        await handle_language_button(update, context)
    elif data == "about":
        from .language import handle_about_button
        await handle_about_button(update, context)
    elif data == "subs":
        from .subscriptions import handle_subscriptions_button
        await handle_subscriptions_button(update, context)
    elif data == "image":
        from .image import handle_image_button
        await handle_image_button(update, context)
    elif data.startswith("lang_"):
        from .about import set_language
        await set_language(update, context, data.split('_')[1])
    elif data == "home":
        await start_handler(update, context)
    else:
        await query.edit_message_text("Unknown action.")

def home_keyboard(user_data):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_data, 'language'), callback_data="lang_menu")],
        [InlineKeyboardButton(get_text(user_data, 'about'), callback_data="about")],
        [InlineKeyboardButton(get_text(user_data, 'subscriptions'), callback_data="subs")],
        [InlineKeyboardButton(get_text(user_data, 'create_image'), callback_data="image")],
        [InlineKeyboardButton(get_text(user_data, 'let_me_updoge'), callback_data="updoge")]
    ])

__all__ = ['start_handler', 'callback_handler']