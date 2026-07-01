import base64
import io
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# --- Inline Keyboards ---
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

# --- Core Logic Functions ---
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
        # Try to decode as UTF-8 text
        decoded_bytes = base64.b64decode(encoded_text)
        decoded_text = decoded_bytes.decode('utf-8')
        return decoded_text, None
    except UnicodeDecodeError:
        # If it's not text, return the bytes for file handling
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
    # A very basic check: look for common image MIME types if it's a data URL
    if encoded_text.startswith('data:image'):
        return True
    # Otherwise, try to decode and check if it looks like an image header
    try:
        decoded = base64.b64decode(encoded_text[:50])  # Check only the beginning
        if decoded.startswith(b'\x89PNG') or decoded.startswith(b'\xff\xd8\xff') or decoded.startswith(b'GIF87a') or decoded.startswith(b'GIF89a'):
            return True
    except:
        pass
    return False
