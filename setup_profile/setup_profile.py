from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
)
from config import get_text
import qrcode
from io import BytesIO
import logging
import sqlite3

# States
NAME, EMAIL, GOAL, SUBSCRIPTION, PAYMENT, CONFIRM = range(6)

# Project wallet (auto-added by bot.py on first run)
PROJECT_WALLET_PUBKEY = None

def get_project_wallet():
    global PROJECT_WALLET_PUBKEY
    if PROJECT_WALLET_PUBKEY is None:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        pubkey_str = os.getenv('PROJECT_WALLET_PUBKEY')
        if pubkey_str:
            PROJECT_WALLET_PUBKEY = pubkey_str
        else:
            raise ValueError("PROJECT_WALLET_PUBKEY not set in .env")
    return PROJECT_WALLET_PUBKEY

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    lang = user_data.get('language', 'en')
    await update.message.reply_text(get_text(user_data, 'profile_start'))
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Enter your email:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text("What’s your goal with UPDOGE? (e.g., hold, trade, meme)")
    return GOAL

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['goal'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Free", callback_data="sub_free")],
        [InlineKeyboardButton("Basic (5000 UPDOGE)", callback_data="sub_basic")],
        [InlineKeyboardButton("Premium (10000 UPDOGE)", callback_data="sub_premium")]
    ]
    await update.message.reply_text("Choose subscription:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SUBSCRIPTION

async def choose_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    
    subs = {
        "sub_free": ("Free", 0),
        "sub_basic": ("Basic", 5000),
        "sub_premium": ("Premium", 10000)
    }
    name, amount = subs[data]
    context.user_data['subscription'] = name
    context.user_data['amount'] = amount
    
    if amount == 0:
        await query.edit_message_text(f"You chose {name} — Free access granted!")
        await save_profile(update, context)
        return ConversationHandler.END
    
    wallet = get_project_wallet()
    qr = qrcode.QRCode()
    qr.add_data(f"solana:{wallet}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="gold", back_color="black")
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    
    await query.message.reply_photo(
        photo=buffer,
        caption=get_text(context.user_data, 'token_payment_prompt', amount=amount, tier=name),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("I Paid", callback_data="paid")
        ]])
    )
    return PAYMENT

async def payment_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Verifying payment on Solana...")
    
    # TODO: Add real transaction verification
    # For now, simulate success
    import asyncio
    await asyncio.sleep(2)
    
    await save_profile(update, context)
    return ConversationHandler.END

async def save_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save to profiles.db
    conn = sqlite3.connect('profiles.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, name TEXT, email TEXT, goal TEXT, subscription TEXT)''')
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
              (update.effective_user.id,
               context.user_data.get('name'),
               context.user_data.get('email'),
               context.user_data.get('goal'),
               context.user_data.get('subscription')))
    conn.commit()
    conn.close()
    
    await update.effective_message.reply_text("Profile saved! You're all set.")

def get_profile_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('profile', start_profile)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            SUBSCRIPTION: [CallbackQueryHandler(choose_subscription)],
            PAYMENT: [CallbackQueryHandler(payment_received, pattern="^paid$")]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )