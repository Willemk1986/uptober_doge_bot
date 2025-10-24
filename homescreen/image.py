import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger("homescreen")

# Logo path
LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'updoge.jpg')

async def handle_image_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting_prompt'] = True
    keyboard = [[InlineKeyboardButton("Cancel", callback_data="home")]]
    await query.edit_message_text(
        "🖼️ *Send a text prompt* (e.g., 'Doge on Mars')\n\nI'll generate a custom UPDOGE image!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_image_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get('awaiting_prompt'):
        return
    context.user_data['awaiting_prompt'] = False

    prompt = update.message.text.strip()
    if len(prompt) > 50:
        prompt = prompt[:47] + "..."

    # Load logo
    try:
        base = Image.open(LOGO_PATH).convert("RGBA")
    except FileNotFoundError:
        base = Image.new("RGBA", (512, 512), (255, 215, 0))  # Gold background
        logger.warning("updoge.jpg missing — using fallback")

    # Add prompt text
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    # Text with shadow
    text_pos = (60, 380)
    shadow_pos = (62, 382)
    draw.text(shadow_pos, prompt, font=font, fill=(0, 0, 0))
    draw.text(text_pos, prompt, font=font, fill=(255, 255, 255))

    # Save to buffer
    buffer = io.BytesIO()
    base.save(buffer, 'PNG')
    buffer.seek(0)

    # Send
    keyboard = [
        [InlineKeyboardButton("New Image", callback_data="image")],
        [InlineKeyboardButton("Share on X", callback_data="share_x")],
        [InlineKeyboardButton("Home", callback_data="home")]
    ]
    await update.message.reply_photo(
        photo=buffer,
        caption=f"🎨 *UPDOGE Image*\n\n\"{prompt}\"\n\n#UPDOGE #Uptober",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )