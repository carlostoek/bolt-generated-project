from aiogram import Router, Bot
from aiogram.types import ChatJoinRequest, ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database.models import PendingChannelRequest, BotConfig
from services.config_service import ConfigService
from services.free_channel_service import FreeChannelService

router = Router()

@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest, bot: Bot, session: AsyncSession):
    """
    Manejar solicitudes de unión al canal gratuito.
    Registra la solicitud para aprobación automática posterior.
    """
    free_service = FreeChannelService(session, bot)
    await free_service.handle_join_request(event)

@router.chat_member()
async def handle_chat_member(update: ChatMemberUpdated, bot: Bot, session: AsyncSession):
    """
    Manejar cambios de membresía en el canal.
    Limpia solicitudes pendientes cuando el usuario se une o sale.
    """
    free_service = FreeChannelService(session, bot)
    free_id = await free_service.get_free_channel_id()
    
    if not free_id or update.chat.id != free_id:
        return

    user_id = update.from_user.id
    status = update.new_chat_member.status
    
    if status in {"member", "administrator", "creator"}:
        # Usuario se unió al canal
        try:
            await bot.send_message(
                user_id, 
                "🎉 **¡Bienvenido al Canal Gratuito!**\n\n"
                "Tu acceso ha sido confirmado exitosamente.\n"
                "¡Disfruta de todo el contenido gratuito disponible!"
            )
        except Exception:
            pass  # Usuario podría tener mensajes privados deshabilitados
        
        # Limpiar solicitud pendiente
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
        if req:
            await session.delete(req)
            await session.commit()
            
    elif status in {"kicked", "left"}:
        # Usuario salió o fue expulsado del canal
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
        if req:
            await session.delete(req)
            await session.commit()
