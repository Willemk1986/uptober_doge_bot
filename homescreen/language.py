from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import get_text
import requests

async def handle_about_button(update, context):
    query = update.callback_query
    await query.answer()  # ← ADD await
    lang = context.user_data.get('language', 'en')
    
    text = get_text(context.user_data, 'about_text', 
                    market_cap="1.2B", 
                    holders="420K", 
                    uptober="UPTOBER 2025")
    
    keyboard = [[InlineKeyboardButton(get_text(context.user_data, 'home'), callback_data="home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')  # ← ADD await