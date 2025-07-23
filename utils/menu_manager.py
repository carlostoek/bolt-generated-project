"""
Advanced menu management system for seamless user experience.
Handles message lifecycle, navigation state, and prevents chat clutter.
"""
import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from utils.message_safety import (
    safe_answer,
    safe_edit,
    safe_send_message,
    safe_edit_message_text,
)
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from database.base_models import User
from database.user_menu_state import set_user_menu_state

logger = logging.getLogger(__name__)

# ... resto del archivo sin cambios ...
