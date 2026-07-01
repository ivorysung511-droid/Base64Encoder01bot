import logging
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import Config
import utils

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=Config.LOG_LEVEL
)
logger = logging.getLogger(__name__)

# --- User State Management ---
user_sessions = {}  # Dictionary to track user states: {user_id: {'mode': 'encode'/'decode', 'action': 'text'/'file'}}

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    user_id = user.id
    # Reset user session
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
        reply_markup=utils.get_mode_keyboard()
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
• The bot will try to detect if a decoded Base64 string is an image and show a preview.
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
        reply_markup=utils.get_mode_keyboard()
    )

# --- Callback Query Handlers ---
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
            reply_markup=utils.get_mode_keyboard()
        )
        return

    if data == "back_to_modes":
        await query.edit_message_text(
            "🔄 Choose an action:",
            reply_markup=utils.get_mode_keyboard()
        )
        return

    if data == "mode_encode":
        user_sessions[user_id]['mode'] = 'encode'
        await query.edit_message_text(
            "📝 **Encode Mode**\n\n"
            "What would you like to encode?",
            parse_mode='Markdown',
            reply_markup=utils.get_action_keyboard('encode')
        )
        return

    if data == "mode_decode":
        user_sessions[user_id]['mode'] = 'decode'
        await query.edit_message_text(
            "🔓 **Decode Mode**\n\n"
            "What would you like to decode?",
            parse_mode='Markdown',
            reply_markup=utils.get_action_keyboard('decode')
        )
        return

    if data == "action_encode_text":
        user_sessions[user_id]['action'] = 'encode_text'
        await query.edit_message_text(
            "✏️ **Encode Text**\n\n"
            "Please send me the text you want to encode to Base64.\n"
            "Type or paste your text below:",
            parse_mode='Markdown',
            reply_markup=utils.get_back_to_start_keyboard()
        )
        return

    if data == "action_decode_text":
        user_sessions[user_id]['action'] = 'decode_text'
        await query.edit_message_text(
            "✏️ **Decode Text**\n\n"
            "Please send me the Base64 string you want to decode.\n"
            "Type or paste the Base64 string below:",
            parse_mode='Markdown',
            reply_markup=utils.get_back_to_start_keyboard()
        )
        return

    if data == "action_encode_file":
        user_sessions[user_id]['action'] = 'encode_file'
        await query.edit_message_text(
            "📎 **Encode File**\n\n"
            "Please upload the file you want to encode to Base64.\n"
            "I accept any file type (images, PDFs, documents, etc.).",
            parse_mode='Markdown',
            reply_markup=utils.get_back_to_start_keyboard()
        )
        return

    if data == "action_decode_file":
        user_sessions[user_id]['action'] = 'decode_file'
        await query.edit_message_text(
            "📎 **Decode File**\n\n"
            "Please upload a `.txt` file containing the Base64 string.\n"
            "I will decode it and attempt to reconstruct the original file.",
            parse_mode='Markdown',
            reply_markup=utils.get_back_to_start_keyboard()
        )
        return

    # Default response
    await query.edit_message_text("Unknown option. Please use /start to restart.")

# --- Message Handlers ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages based on the user's current state."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        await update.message.reply_text(
            "🚀 Let's start! Use /start to begin.",
            reply_markup=utils.get_mode_keyboard()
        )
        return

    user_state = user_sessions[user_id]
    action = user_state.get('action')

    if action == 'encode_text':
        result, error = utils.encode_text(text)
        if error:
            await update.message.reply_text(f"❌ {error}\n\nPlease try again or /cancel.")
        else:
            # Send the result in a code block
            await update.message.reply_text(
                f"✅ **Encoded Text (Base64):**\n\n"
                f"`{result}`\n\n"
                f"📋 Copy the string above.",
                parse_mode='Markdown'
            )
        # Reset action to avoid accidental re-processing
        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=utils.get_mode_keyboard()
        )

    elif action == 'decode_text':
        result, error = utils.decode_text(text)
        if error:
            await update.message.reply_text(f"❌ {error}\n\nPlease check your Base64 string and try again.")
        elif result == "binary":
            await update.message.reply_text(
                "⚠️ The decoded data appears to be binary (not text).\n"
                "Try decoding it as a file instead."
            )
        else:
            # Check if the decoded text might be an image (data URL)
            if text.startswith('data:image') or utils.is_base64_image(text):
                # For simplicity, we'll just show a note. We could implement image preview by decoding bytes.
                await update.message.reply_text(
                    f"✅ **Decoded Text:**\n\n"
                    f"`{result}`\n\n"
                    f"💡 *Note: Your Base64 seems to represent an image. For preview, try decoding as a file.*",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"✅ **Decoded Text:**\n\n"
                    f"`{result}`",
                    parse_mode='Markdown'
                )
        # Reset action
        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=utils.get_mode_keyboard()
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

    # Get the file object
    if update.message.document:
        file = update.message.document
        file_name = file.file_name or "document"
    elif update.message.photo:
        # Handle photo - get the largest size
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
            # Download the file
            file_obj = await context.bot.get_file(file.file_id)
            file_bytes = await file_obj.download_as_bytearray()

            # Encode to Base64
            encoded_result, error = utils.encode_file(bytes(file_bytes))
            if error:
                await update.message.reply_text(f"❌ {error}")
                return

            # Send the result as a text file to avoid overwhelming the chat
            filename = f"{file_name}.base64.txt"
            await update.message.reply_document(
                document=io.BytesIO(encoded_result.encode('utf-8')),
                filename=filename,
                caption=f"✅ **Base64 Encoded:** {file_name}\n\nThe encoded string is in the attached file."
            )
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            await update.message.reply_text(f"❌ Error processing file: {str(e)}")

        # Reset action
        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=utils.get_mode_keyboard()
        )

    elif action == 'decode_file':
        # Decoding a file - we expect a .txt file containing the Base64 string
        if not file_name.endswith('.txt') and file.mime_type != 'text/plain':
            await update.message.reply_text(
                "⚠️ For decoding, please send a `.txt` file containing the Base64 string."
            )
            return

        try:
            # Download the file content
            file_obj = await context.bot.get_file(file.file_id)
            file_content = await file_obj.download_as_bytearray()
            base64_string = file_content.decode('utf-8').strip()

            # Decode the Base64
            decoded_bytes, error = utils.decode_file(base64_string)
            if error:
                await update.message.reply_text(f"❌ {error}")
                return

            # Try to determine file type and send it back
            # We'll send it as a generic file; user can rename it
            response_filename = "decoded_file.bin"
            # Basic check for image headers to suggest a name
            if decoded_bytes.startswith(b'\x89PNG'):
                response_filename = "decoded_image.png"
            elif decoded_bytes.startswith(b'\xff\xd8\xff'):
                response_filename = "decoded_image.jpg"
            elif decoded_bytes.startswith(b'GIF87a') or decoded_bytes.startswith(b'GIF89a'):
                response_filename = "decoded_image.gif"

            # Send the decoded file
            await update.message.reply_document(
                document=io.BytesIO(decoded_bytes),
                filename=response_filename,
                caption=f"✅ **Decoded File:** Successfully reconstructed from Base64."
            )

        except Exception as e:
            logger.error(f"Error decoding file: {str(e)}")
            await update.message.reply_text(f"❌ Error decoding file: {str(e)}")

        # Reset action
        user_sessions[user_id]['action'] = None
        await update.message.reply_text(
            "🔁 What would you like to do next?",
            reply_markup=utils.get_mode_keyboard()
        )

    else:
        # If the user hasn't selected a specific action, ask them what to do
        await update.message.reply_text(
            "📎 I see you sent a file. Use /start to choose a mode first."
        )

def main():
    """Start the bot."""
    logger.info("Starting Base64 Encoder/Decoder Bot...")

    # Create the Application
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Add callback query handler for all button presses
    application.add_handler(CallbackQueryHandler(button_handler))

    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_message))

    # Start the bot
    logger.info("Bot is running and polling for updates...")
    application.run_polling()

if __name__ == '__main__':
    main()
