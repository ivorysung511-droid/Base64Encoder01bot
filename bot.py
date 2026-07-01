import os
import io
import base64
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables.")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== USER STATE MANAGEMENT ====================
user_sessions = {}

# ==================== KEYBOARD FUNCTIONS ====================
def get_mode_keyboard():
    """Returns the inline keyboard for mode selection."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Encode to Base64", callback_data="mode_encode"),
            InlineKeyboardButton("🔓 Decode from Base64", callback_data="mode_decode"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_action_keyboard(action_type):
    """Returns the appropriate action keyboard."""
    if action_type == "encode":
        keyboard = [
            [
                InlineKeyboardButton("📝 Encode Text", callback_data="action_encode_text"),
                InlineKeyboardButton("📎 Encode File", callback_data="action_encode_file"),
            ],
            [InlineKeyboardButton("🔙 Back to Modes", callback_data="back_to_modes")],
        ]
    else:  # decode
        keyboard = [
            [
                InlineKeyboardButton("📝 Decode Text", callback_data="action_decode_text"),
                InlineKeyboardButton("📎 Decode File", callback_data="action_decode_file"),
            ],
            [InlineKeyboardButton("🔙 Back to Modes", callback_data="back_to_modes")],
        ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_start_keyboard():
    """Keyboard to go back to the start menu."""
    keyboard = [[InlineKeyboardButton("🏠 Back to Start", callback_data="back_to_start")]]
    return InlineKeyboardMarkup(keyboard)

# ==================== BASE64 FUNCTIONS ====================
def encode_text(text):
    """Encodes a text string to Base64."""
    try:
        text_bytes = text.encode('utf-8')
        encoded_bytes = base64.b64encode(text_bytes)
        return encoded_bytes.decode('utf-8'), None
    except Exception as e:
        return None, f"Error encoding text: {str(e)}"

def decode_text(encoded_text):
    """Decodes a Base64 string back to text."""
    try:
        decoded_bytes = base64.b64decode(encoded_text)
        decoded_text = decoded_bytes.decode('utf-8')
        return decoded_text, None
    except UnicodeDecodeError:
        try:
            decoded_bytes = base64.b64decode(encoded_text)
            return decoded_bytes, "binary"
        except Exception as e:
            return None, f"Error decoding Base64: {str(e)}"
    except Exception as e:
        return None, f"Error decoding Base64: {str(e)}"

def encode_file(file_bytes):
    """Encodes file bytes to Base64."""
    try:
        encoded_bytes = base64.b64encode(file_bytes)
        return encoded_bytes.decode('utf-8'), None
    except Exception as e:
        return None, f"Error encoding file: {str(e)}"

def decode_file(encoded_text):
    """Decodes Base64 string back to bytes for file reconstruction."""
    try:
        decoded_bytes = base64.b64decode(encoded_text)
        return decoded_bytes, None
    except Exception as e:
        return None, f"Error decoding Base64 for file: {str(e)}"

def is_base64_image(encoded_text):
    """Checks if the encoded text might represent an image."""
    try:
        decoded = base64.b64decode(encoded_text[:50])
        if (decoded.startswith(b'\x89PNG') or 
            decoded.startswith(b'\xff\xd8\xff') or 
            decoded.startswith(b'GIF87a') or 
            decoded.startswith(b'GIF89a')):
            return True
    except:
        pass
    return False

# ==================== COMMAND HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    user_id = user.id
    user_sessions[user_id] = {}

    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        f"I am a **Base64 Encoder/Decoder Bot**.\n"
        f"Choose what you want to do:\n"
        f"• Encode text or a file to Base64\n"
        f"• Decode Base64 back to text or a file\n\n"
        f"Select an option below:"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_mode_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    help_text = """
🤖 **Base64 Encoder/Decoder Bot - Help**

**Commands:**
/start - Start the bot and select a mode
/help - Show this help message
/about - About this bot
/cancel - Cancel current operation

**How to use:**
1. Choose **Encode** to convert text or a file to Base64.
2. Choose **Decode** to convert Base64 back to text or a file.

**Tips:**
• For decoding, you can send a Base64 string or a `.txt` file containing it.
• The bot will try to detect if a decoded Base64 string is an image.
• Maximum file size is determined by Telegram (usually 50MB for files).
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /about command."""
    about_text = """
⚡ **Base64 Encoder/Decoder Bot**

A simple and secure tool to encode and decode Base64.

**Features:**
• Encode/Decode text instantly
• Encode/Decode files (images, documents, etc.)
• Preview for Base64-encoded images

**Tech Stack:**
• Python + python-telegram-bot
• Deployed on Railway

**Developer:** @YourUsername
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /cancel command to reset user state."""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text(
        "🔄 Operation cancelled. Use /start to begin again.",
        reply_markup=get_mode_keyboard()
    )

# ==================== CALLBACK QUERY HANDLERS ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all button callback queries."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "back_to_start":
        user_sessions[user_id] = {}
        await query.edit_message_text(
            "🔄 Returning to main menu. Choose an option:",
            reply_markup=get_mode_keyboard()
        )
        return

    if data == "back_to_modes":
        await query.edit_message_text(
            "🔄 Choose an action:",
            reply_markup=get_mode_keyboard()
        )
        return

    if data == "mode_encode":
        user_sessions[user_id]['mode'] = 'encode'
        await query.edit_message_text(
            "📝 **Encode Mode**\n\n"
            "What would you like to encode?",
            parse_mode='Markdown',
            reply_markup=get_action_keyboard('encode')
        )
        return

    if data == "mode_decode":
        user_sessions[user_id]['mode'] = 'decode'
        await query.edit_message_text(
            "🔓 **Decode Mode**\n\n"
            "What would you like to decode?",
            parse_mode='Markdown',
            reply_markup=get_action_keyboard('decode')
        )
        return

    if data == "action_encode_text":
        user_sessions[user_id]['action'] = 'encode_text'
        await query.edit_message_text(
            "✏️ **Encode Text**\n\n"
            "Please send me the text you want to encode to Base64.\n"
            "Type or paste your text below:",
            parse_mode='Markdown',
            reply_markup=get_back_to_start_keyboard()
        )
        return

    if data == "action_decode_text":
        user_sessions[user_id]['action'] = 'decode_text'
        await query.edit_message_text(
            "✏️ **Decode Text**\n\n"
            "Please send me the Base64 string you want to decode.\n"
            "Type or paste the Base64 string below:",
            parse_mode='Markdown',
            reply_markup=get_back_to_start_keyboard()
        )
        return

    if data == "action_encode_file":
        user_sessions[user_id]['action'] = 'encode_file'
        await query.edit_message_text(
            "📎 **Encode File**\n\n"
            "Please upload the file you want to encode to Base64.\n"
            "I accept any file type (images, PDFs, documents, etc.).",
            parse_mode='Markdown',
            reply_markup=get_back_to_start_keyboard()
        )
        return

    if data == "action_decode_file":
        user_sessions[user_id]['action'] = 'decode_file'
        await query.edit_message_text(
            "📎 **Decode File**\n\n"
            "Please upload a `.txt` file containing the Base64 string.\n"
            "I will decode it and attempt to reconstruct the original file.",
            parse_mode='Markdown',
            reply_markup=get_back_to_start_keyboard()
        )
        return

    await query.edit_message_text("Unknown option. Please use /start to restart.")

# ==================== MESSAGE HANDLERS ====================
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages based on the user's current state."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        await update.message.reply_text(
            "🚀 Let's start! Use /start to begin.",
            reply_markup=get_mode_keyboard()
        )
        return

    user_state = user_sessions[user_id]
    action = user_state.get('action')

    if action == 'encode_text':
        result, error = encode_text(text)
        if error:
            await update.message.reply_text(f"❌ {error}\n\nPlease try again or /cancel.")
        else:
            await update.message.reply_text(
                f"✅ **Encoded Text (Base64):**\n\n"
                f"`{result}`\n\n"
                f"📋 Copy the string above.",
                parse_mode='Markdown'
            )
        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=get_mode_keyboard()
        )

    elif action == 'decode_text':
        result, error = decode_text(text)
        if error:
            await update.message.reply_text(f"❌ {error}\n\nPlease check your Base64 string and try again.")
        elif result == "binary":
            await update.message.reply_text(
                "⚠️ The decoded data appears to be binary (not text).\n"
                "Try decoding it as a file instead."
            )
        else:
            if is_base64_image(text):
                await update.message.reply_text(
                    f"✅ **Decoded Text:**\n\n"
                    f"`{result}`\n\n"
                    f"💡 *Note: Your Base64 seems to represent an image.*",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"✅ **Decoded Text:**\n\n"
                    f"`{result}`",
                    parse_mode='Markdown'
                )
        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=get_mode_keyboard()
        )

    else:
        await update.message.reply_text(
            "❓ I'm not sure what to do with this. Use the buttons or /help."
        )

async def handle_file_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles file uploads based on the user's current state."""
    user_id = update.effective_user.id
    file = None
    file_name = "file"

    if update.message.document:
        file = update.message.document
        file_name = file.file_name or "document"
    elif update.message.photo:
        file = update.message.photo[-1]
        file_name = "image.jpg"
    else:
        await update.message.reply_text("❌ Unsupported file type. Please send a document or photo.")
        return

    if user_id not in user_sessions:
        await update.message.reply_text("🚀 Use /start to begin.")
        return

    user_state = user_sessions[user_id]
    action = user_state.get('action')

    if action == 'encode_file':
        try:
            file_obj = await context.bot.get_file(file.file_id)
            file_bytes = await file_obj.download_as_bytearray()
            encoded_result, error = encode_file(bytes(file_bytes))
            if error:
                await update.message.reply_text(f"❌ {error}")
                return

            filename = f"{file_name}.base64.txt"
            await update.message.reply_document(
                document=io.BytesIO(encoded_result.encode('utf-8')),
                filename=filename,
                caption=f"✅ **Base64 Encoded:** {file_name}\n\nThe encoded string is in the attached file."
            )
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            await update.message.reply_text(f"❌ Error processing file: {str(e)}")

        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=get_mode_keyboard()
        )

    elif action == 'decode_file':
        if not file_name.endswith('.txt') and file.mime_type != 'text/plain':
            await update.message.reply_text(
                "⚠️ For decoding, please send a `.txt` file containing the Base64 string."
            )
            return

        try:
            file_obj = await context.bot.get_file(file.file_id)
            file_content = await file_obj.download_as_bytearray()
            base64_string = file_content.decode('utf-8').strip()

            decoded_bytes, error = decode_file(base64_string)
            if error:
                await update.message.reply_text(f"❌ {error}")
                return

            response_filename = "decoded_file.bin"
            if decoded_bytes.startswith(b'\x89PNG'):
                response_filename = "decoded_image.png"
            elif decoded_bytes.startswith(b'\xff\xd8\xff'):
                response_filename = "decoded_image.jpg"
            elif decoded_bytes.startswith(b'GIF87a') or decoded_bytes.startswith(b'GIF89a'):
                response_filename = "decoded_image.gif"

            await update.message.reply_document(
                document=io.BytesIO(decoded_bytes),
                filename=response_filename,
                caption=f"✅ **Decoded File:** Successfully reconstructed from Base64."
            )

        except Exception as e:
            logger.error(f"Error decoding file: {str(e)}")
            await update.message.reply_text(f"❌ Error decoding file: {str(e)}")

        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=get_mode_keyboard()
        )

    else:
        await update.message.reply_text(
            "📎 I see you sent a file. Use /start to choose a mode first."
        )

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot."""
    logger.info("Starting Base64 Encoder/Decoder Bot...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_message))

    logger.info("Bot is running and polling for updates...")
    application.run_polling()

if __name__ == '__main__':
    main()
