from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import get_text

async def handle_language_button(update, context):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("Español", callback_data="lang_es")],
        [InlineKeyboardButton(get_text(context.user_data, 'home'), callback_data="home")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose language:", reply_markup=reply_markup)

async def set_language(update, context, lang_code):
    query = update.callback_query
    await query.answer()
    context.user_data['language'] = lang_code
    from .homescreen import start_handler  # ← Use start_handler, not show_homescreen
    await start_handler(update, context)