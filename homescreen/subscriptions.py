from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import get_text

def handle_subscriptions_button(update, context):
    query = update.callback_query
    query.answer()
    
    tiers = [
        ("Free", "0 UPDOGE", "Basic features"),
        ("Basic", "5000 UPDOGE", "Image gen, tweets"),
        ("Premium", "10000 UPDOGE", "AI images, priority")
    ]
    
    text = "<b>Subscription Tiers</b>\n\n"
    for name, cost, desc in tiers:
        text += f"<b>{name}</b>: {cost}\n{desc}\n\n"
    
    keyboard = [[InlineKeyboardButton(get_text(context.user_data, 'home'), callback_data="home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')