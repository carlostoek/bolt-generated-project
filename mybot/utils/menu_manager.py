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
from database.models import User, set_user_menu_state

logger = logging.getLogger(__name__)

class MenuManager:
    """
    Centralized menu management system that ensures clean chat experience.
    - Only one active menu message per user
    - Automatic cleanup of temporary messages
    - Smooth navigation without message proliferation
    """
    
    def __init__(self):
        # Store the current menu message for each user
        self._active_menus: Dict[int, Tuple[int, int]] = {}  # user_id -> (chat_id, message_id)
        # Store temporary messages that should be auto-deleted
        self._temp_messages: Dict[int, Tuple[int, int, float]] = {}  # user_id -> (chat_id, message_id, expire_time)
        # Navigation history for back button functionality
        self._nav_history: Dict[int, list] = {}  # user_id -> [menu_states]
    
    async def show_menu(
        self, 
        message: Message, 
        text: str, 
        keyboard: InlineKeyboardMarkup,
        session: AsyncSession,
        menu_state: str,
        parse_mode: str = "Markdown",
        # NUEVO PARÁMETRO: Indicar si se debe eliminar el mensaje original (ej. el comando /start)
        delete_origin_message: bool = False 
    ) -> Message:
        """
        Display a menu, replacing any existing menu for this user.
        This ensures only one menu message exists per user.
        If delete_origin_message is True, attempts to delete the message
        that triggered this menu display (e.g., a command).
        """
        user_id = message.from_user.id
        bot = message.bot
        
        # Clean up any temporary messages first
        await self._cleanup_temp_messages(bot, user_id)
        
        # Try to update existing menu if it exists
        existing = self._active_menus.get(user_id)
        if existing:
            chat_id, msg_id = existing
            try:
                # Intenta editar el mensaje del menú *anterior*
                await safe_edit_message_text(
                    bot,
                    chat_id,
                    msg_id,
                    text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode,
                )
                await set_user_menu_state(session, user_id, menu_state)
                
                # Si el origen es un comando y se debe eliminar, lo hacemos aquí.
                if delete_origin_message and message.message_id:
                    try:
                        await bot.delete_message(message.chat.id, message.message_id)
                    except TelegramAPIError as e:
                        logger.warning(f"Could not delete origin message {message.message_id} for user {user_id}: {e}")
                return None  # Message was updated, no new message sent
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    # Si el mensaje no ha cambiado, no hay necesidad de hacer nada.
                    if delete_origin_message and message.message_id:
                        try:
                            await bot.delete_message(message.chat.id, message.message_id)
                        except TelegramAPIError as e:
                            logger.warning(f"Could not delete origin message {message.message_id} for user {user_id}: {e}")
                    return None
                # El mensaje no se pudo editar (ej. fue borrado por el usuario), así que necesitamos enviar uno nuevo.
                logger.debug(f"Could not update menu for user {user_id} (will create new): {e}")
            except Exception as e:
                logger.error(f"Error updating menu for user {user_id}, falling back to create new: {e}")
        
        # Create new menu message (either because no existing, or update failed)
        try:
            sent_message = await safe_answer(
                message,
                text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            self._active_menus[user_id] = (sent_message.chat.id, sent_message.message_id)
            await set_user_menu_state(session, user_id, menu_state)
            
            # Update navigation history
            self._update_nav_history(user_id, menu_state)
            
            # Delete the original command message if requested
            if delete_origin_message and message.message_id:
                try:
                    await bot.delete_message(message.chat.id, message.message_id)
                except TelegramAPIError as e:
                    logger.warning(f"Could not delete origin message {message.message_id} for user {user_id}: {e}")
            
            return sent_message
        except Exception as e:
            logger.error(f"Error creating menu for user {user_id}: {e}")
            raise
    
    async def update_menu(
        self,
        callback: CallbackQuery,
        text: str,
        keyboard: InlineKeyboardMarkup,
        session: AsyncSession,
        menu_state: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Update the current menu via callback query.
        Returns True if successful, False otherwise.
        """
        user_id = callback.from_user.id
        bot = callback.bot
        message = callback.message # This is the message that contains the inline keyboard
        
        # Clean up any temporary messages
        await self._cleanup_temp_messages(bot, user_id)
        
        try:
            await safe_edit(
                message,
                text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            
            # Update stored menu reference - this is crucial to ensure _active_menus points to the correct message
            self._active_menus[user_id] = (message.chat.id, message.message_id) # Corregido de message.message.id a message.message_id
            await set_user_menu_state(session, user_id, menu_state)
            
            # Update navigation history
            self._update_nav_history(user_id, menu_state)
            
            return True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return True  # No change needed
            logger.error(f"Error updating menu for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating menu for user {user_id}: {e}")
            return False
    
    async def send_temporary_message(
        self,
        message: Message,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        auto_delete_seconds: int = 5,
        parse_mode: str = "Markdown"
    ) -> Message:
        """
        Send a temporary message that will be automatically deleted.
        Useful for error messages, confirmations, etc.
        """
        user_id = message.from_user.id
        bot = message.bot
        
        # Clean up previous temporary message
        await self._cleanup_temp_messages(bot, user_id)
        
        try:
            sent_message = await safe_answer(
                message,
                text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            
            # Schedule for deletion
            import time
            expire_time = time.time() + auto_delete_seconds
            self._temp_messages[user_id] = (sent_message.chat.id, sent_message.message_id, expire_time)
            
            # Schedule actual deletion
            asyncio.create_task(self._auto_delete_message(bot, user_id, auto_delete_seconds))
            
            return sent_message
        except Exception as e:
            logger.error(f"Error sending temporary message for user {user_id}: {e}")
            raise
    
    async def go_back(
        self,
        callback: CallbackQuery,
        session: AsyncSession,
        default_menu_state: str = "main"
    ) -> bool:
        """
        Navigate back to the previous menu in the history.
        """
        user_id = callback.from_user.id
        history = self._nav_history.get(user_id, [])
        
        # Ensure we always have at least one state (the current one) if history is not empty
        if len(history) > 1:
            # Remove current state
            history.pop() 
            previous_state = history[-1]
        elif len(history) == 1:
            # If only one item, it means we are at the "root" of the history for this session.
            # We should try to go back to it, but not pop it.
            previous_state = history[0] # Stay at the current state
            logger.debug(f"User {user_id} is at the start of navigation history. Staying at '{previous_state}'.")
        else:
            previous_state = default_menu_state
            logger.debug(f"User {user_id} has no navigation history. Falling back to default: '{default_menu_state}'.")
        
        # Import here to avoid circular imports
        from utils.menu_factory import menu_factory # Usa la instancia global si existe
        
        try:
            # create_menu necesita 'bot' para ciertas lógicas de texto/teclado.
            # Pasamos callback.bot
            text, keyboard = await menu_factory.create_menu(previous_state, callback.from_user.id, session, callback.bot)
            return await self.update_menu(callback, text, keyboard, session, previous_state)
        except Exception as e:
            logger.error(f"Error going back for user {user_id}: {e}")
            return False
    
    async def clear_user_data(self, user_id: int, bot) -> None:
        """
        Clear all stored data for a user (menus, temp messages, history).
        Useful when user logs out or resets.
        """
        # Clean up temporary messages
        await self._cleanup_temp_messages(bot, user_id)
        
        # Remove active menu reference
        self._active_menus.pop(user_id, None)
        
        # Clear navigation history
        self._nav_history.pop(user_id, None)
    
    def _update_nav_history(self, user_id: int, menu_state: str) -> None:
        """Update navigation history for back button functionality."""
        if user_id not in self._nav_history:
            self._nav_history[user_id] = []
        
        history = self._nav_history[user_id]
        
        # Don't add duplicate consecutive states
        if not history or history[-1] != menu_state:
            history.append(menu_state)
            
            # Limit history size to prevent memory issues
            if len(history) > 10: # Keep a reasonable history length
                history.pop(0)
    
    async def _cleanup_temp_messages(self, bot, user_id: int) -> None:
        """Clean up expired temporary messages for a user."""
        temp_msg = self._temp_messages.get(user_id)
        if temp_msg:
            chat_id, msg_id, expire_time = temp_msg
            import time
            if time.time() >= expire_time:
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass  # Message might already be deleted or not found
                finally:
                    self._temp_messages.pop(user_id, None)
    
    async def _auto_delete_message(self, bot, user_id: int, delay: int) -> None:
        """Auto-delete a temporary message after delay."""
        await asyncio.sleep(delay)
        await self._cleanup_temp_messages(bot, user_id)

# Global menu manager instance
menu_manager = MenuManager()
