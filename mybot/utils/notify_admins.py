import logging
from aiogram import Bot
from utils.config import ADMIN_IDS


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")
