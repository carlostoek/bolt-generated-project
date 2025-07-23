"""
Servicio para gestión completa del canal gratuito.
Incluye aprobación automática, envío de mensajes y protección de contenido.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from aiogram import Bot
from aiogram.types import (
    ChatJoinRequest, 
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio
)
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import PendingChannelRequest, User, BotConfig
from services.config_service import ConfigService
from services.message_registry import store_message
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)


class FreeChannelService:
    """
    Servicio completo para gestión del canal gratuito.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.config_service = ConfigService(session)
    
    async def get_free_channel_id(self) -> Optional[int]:
        """Obtener ID del canal gratuito configurado."""
        return await self.config_service.get_free_channel_id()
    
    async def set_free_channel_id(self, channel_id: int) -> bool:
        """Configurar el canal gratuito."""
        try:
            await self.config_service.set_free_channel_id(channel_id)
            logger.info(f"Free channel configured: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting free channel ID: {e}")
            return False
    
    async def get_wait_time_minutes(self) -> int:
        """Obtener tiempo de espera configurado para aprobaciones."""
        config = await self.session.get(BotConfig, 1)
        return config.free_channel_wait_time_minutes if config else 0
    
    async def set_wait_time_minutes(self, minutes: int) -> bool:
        """Configurar tiempo de espera para aprobaciones."""
        try:
            config = await self.session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1, free_channel_wait_time_minutes=minutes)
                self.session.add(config)
            else:
                config.free_channel_wait_time_minutes = minutes
            
            await self.session.commit()
            logger.info(f"Wait time set to {minutes} minutes")
            return True
        except Exception as e:
            logger.error(f"Error setting wait time: {e}")
            return False
    
    async def handle_join_request(self, join_request: ChatJoinRequest) -> bool:
        """
        Procesar solicitud de unión al canal gratuito.
        Registra la solicitud para aprobación automática posterior.
        """
        free_channel_id = await self.get_free_channel_id()
        if not free_channel_id or join_request.chat.id != free_channel_id:
            return False
        
        user_id = join_request.from_user.id
        
        try:
            # Verificar si ya existe una solicitud pendiente
            existing_stmt = select(PendingChannelRequest).where(
                PendingChannelRequest.user_id == user_id,
                PendingChannelRequest.chat_id == join_request.chat.id,
                PendingChannelRequest.approved == False
            )
            existing_result = await self.session.execute(existing_stmt)
            existing_request = existing_result.scalar_one_or_none()
            
            if existing_request:
                logger.info(f"User {user_id} already has pending request for channel {join_request.chat.id}")
                return True
            
            # Crear nueva solicitud pendiente
            pending_request = PendingChannelRequest(
                user_id=user_id,
                chat_id=join_request.chat.id,
                request_timestamp=datetime.utcnow(),
                approved=False
            )
            
            self.session.add(pending_request)
            await self.session.commit()
            
            # Notificar al usuario sobre el tiempo de espera
            wait_minutes = await self.get_wait_time_minutes()
            
            if wait_minutes > 0:
                wait_text = f"{wait_minutes} minutos"
                if wait_minutes >= 60:
                    hours = wait_minutes // 60
                    remaining_minutes = wait_minutes % 60
                    if remaining_minutes > 0:
                        wait_text = f"{hours} horas y {remaining_minutes} minutos"
                    else:
                        wait_text = f"{hours} horas"
                
                notification_message = (
                    f"📋 **Solicitud Recibida**\n\n"
                    f"Tu solicitud para unirte al canal gratuito ha sido registrada.\n\n"
                    f"⏰ **Tiempo de espera**: {wait_text}\n"
                    f"✅ Serás aprobado automáticamente una vez transcurrido este tiempo.\n\n"
                    f"¡Gracias por tu paciencia!"
                )
            else:
                notification_message = (
                    f"📋 **Solicitud Recibida**\n\n"
                    f"Tu solicitud para unirte al canal gratuito ha sido registrada.\n\n"
                    f"✅ Serás aprobado inmediatamente.\n\n"
                    f"¡Bienvenido!"
                )
            
            try:
                await self.bot.send_message(
                    user_id,
                    notification_message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Could not notify user {user_id} about join request: {e}")
            
            logger.info(f"Join request registered for user {user_id} in channel {join_request.chat.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling join request for user {user_id}: {e}")
            return False
    
    async def process_pending_requests(self) -> int:
        """
        Procesar solicitudes pendientes que han cumplido el tiempo de espera.
        Retorna el número de solicitudes procesadas.
        """
        wait_minutes = await self.get_wait_time_minutes()
        threshold_time = datetime.utcnow() - timedelta(minutes=wait_minutes)
        
        # Obtener solicitudes que han cumplido el tiempo de espera
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.approved == False,
            PendingChannelRequest.request_timestamp <= threshold_time
        )
        
        result = await self.session.execute(stmt)
        pending_requests = result.scalars().all()
        
        processed_count = 0
        
        for request in pending_requests:
            try:
                # Aprobar la solicitud en Telegram
                await self.bot.approve_chat_join_request(
                    request.chat_id, 
                    request.user_id
                )
                
                # Marcar como aprobada en la base de datos
                request.approved = True
                
                # Enviar mensaje de bienvenida
                welcome_message = (
                    f"🎉 **¡Bienvenido al Canal Gratuito!**\n\n"
                    f"Tu solicitud ha sido aprobada exitosamente.\n"
                    f"Ya puedes acceder a todo el contenido gratuito.\n\n"
                    f"¡Disfruta de la experiencia!"
                )
                
                try:
                    await self.bot.send_message(
                        request.user_id,
                        welcome_message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Could not send welcome message to user {request.user_id}: {e}")
                
                processed_count += 1
                logger.info(f"Approved join request for user {request.user_id} in channel {request.chat_id}")
                
            except TelegramBadRequest as e:
                if "USER_ALREADY_PARTICIPANT" in str(e):
                    # Usuario ya está en el canal, marcar como aprobado
                    request.approved = True
                    processed_count += 1
                    logger.info(f"User {request.user_id} already in channel {request.chat_id}")
                else:
                    logger.error(f"Error approving join request for user {request.user_id}: {e}")
            except Exception as e:
                logger.error(f"Error processing join request for user {request.user_id}: {e}")
        
        if processed_count > 0:
            await self.session.commit()
            logger.info(f"Processed {processed_count} pending join requests")
        
        return processed_count
    
    async def create_invite_link(
        self, 
        expire_hours: int = 24, 
        member_limit: Optional[int] = None,
        creates_join_request: bool = True
    ) -> Optional[str]:
        """
        Crear enlace de invitación para el canal gratuito.
        """
        free_channel_id = await self.get_free_channel_id()
        if not free_channel_id:
            logger.error("Free channel not configured")
            return None
        
        try:
            expire_date = datetime.utcnow() + timedelta(hours=expire_hours)
            
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=free_channel_id,
                expire_date=expire_date,
                member_limit=member_limit,
                creates_join_request=creates_join_request,
                name=f"Enlace Gratuito - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
            logger.info(f"Created invite link for free channel: {invite_link.invite_link}")
            return invite_link.invite_link
            
        except Exception as e:
            logger.error(f"Error creating invite link for free channel: {e}")
            return None
    
    async def send_message_to_channel(
        self,
        text: str,
        protect_content: bool = True,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        media_files: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Message]:
        """
        Enviar mensaje al canal gratuito con protección opcional.
        
        Args:
            text: Texto del mensaje
            protect_content: Si proteger el contenido (no se puede reenviar/copiar)
            reply_markup: Teclado inline opcional
            media_files: Lista de archivos multimedia [{'type': 'photo/video/document/audio', 'file_id': 'xxx', 'caption': 'xxx'}]
        """
        free_channel_id = await self.get_free_channel_id()
        if not free_channel_id:
            logger.error("Free channel not configured")
            return None
        
        try:
            # Si hay archivos multimedia, enviar como álbum
            if media_files and len(media_files) > 1:
                media_group = []
                for i, media in enumerate(media_files[:10]):  # Máximo 10 archivos
                    media_type = media.get('type', 'photo')
                    file_id = media.get('file_id')
                    caption = media.get('caption', text if i == 0 else None)
                    
                    if media_type == 'photo':
                        media_group.append(InputMediaPhoto(media=file_id, caption=caption))
                    elif media_type == 'video':
                        media_group.append(InputMediaVideo(media=file_id, caption=caption))
                    elif media_type == 'document':
                        media_group.append(InputMediaDocument(media=file_id, caption=caption))
                    elif media_type == 'audio':
                        media_group.append(InputMediaAudio(media=file_id, caption=caption))
                
                if media_group:
                    messages = await self.bot.send_media_group(
                        chat_id=free_channel_id,
                        media=media_group,
                        protect_content=protect_content
                    )
                    logger.info(f"Sent media group to free channel: {len(messages)} messages")
                    return messages[0] if messages else None
            
            # Si hay un solo archivo multimedia
            elif media_files and len(media_files) == 1:
                media = media_files[0]
                media_type = media.get('type', 'photo')
                file_id = media.get('file_id')
                
                if media_type == 'photo':
                    sent_message = await self.bot.send_photo(
                        chat_id=free_channel_id,
                        photo=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                elif media_type == 'video':
                    sent_message = await self.bot.send_video(
                        chat_id=free_channel_id,
                        video=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                elif media_type == 'document':
                    sent_message = await self.bot.send_document(
                        chat_id=free_channel_id,
                        document=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                elif media_type == 'audio':
                    sent_message = await self.bot.send_audio(
                        chat_id=free_channel_id,
                        audio=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                else:
                    # Fallback a mensaje de texto
                    sent_message = await self.bot.send_message(
                        chat_id=free_channel_id,
                        text=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
            else:
                # Mensaje de texto simple
                sent_message = await self.bot.send_message(
                    chat_id=free_channel_id,
                    text=text,
                    reply_markup=reply_markup,
                    protect_content=protect_content,
                    parse_mode="Markdown"
                )
            
            logger.info(f"Message sent to free channel: {sent_message.message_id}")
            if reply_markup:
                store_message(free_channel_id, sent_message.message_id)
            return sent_message
            
        except Exception as e:
            logger.error(f"Error sending message to free channel: {e}")
            return None
    
    async def get_channel_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del canal gratuito."""
        free_channel_id = await self.get_free_channel_id()
        
        stats = {
            "channel_configured": bool(free_channel_id),
            "channel_id": free_channel_id,
            "pending_requests": 0,
            "total_processed": 0,
            "wait_time_minutes": await self.get_wait_time_minutes()
        }
        
        if free_channel_id:
            try:
                # Contar solicitudes pendientes
                pending_stmt = select(func.count()).select_from(PendingChannelRequest).where(
                    PendingChannelRequest.chat_id == free_channel_id,
                    PendingChannelRequest.approved == False
                )
                pending_result = await self.session.execute(pending_stmt)
                stats["pending_requests"] = pending_result.scalar() or 0
                
                # Contar total procesadas
                total_stmt = select(func.count()).select_from(PendingChannelRequest).where(
                    PendingChannelRequest.chat_id == free_channel_id,
                    PendingChannelRequest.approved == True
                )
                total_result = await self.session.execute(total_stmt)
                stats["total_processed"] = total_result.scalar() or 0
                
                # Información del canal
                try:
                    chat_info = await self.bot.get_chat(free_channel_id)
                    stats["channel_title"] = chat_info.title
                    stats["channel_username"] = chat_info.username
                    stats["channel_member_count"] = await self.bot.get_chat_member_count(free_channel_id)
                except Exception as e:
                    logger.warning(f"Could not get channel info: {e}")
                    
            except Exception as e:
                logger.error(f"Error getting channel statistics: {e}")
        
        return stats
    
    async def cleanup_old_requests(self, days_old: int = 30) -> int:
        """
        Limpiar solicitudes antiguas de la base de datos.
        Retorna el número de solicitudes eliminadas.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        try:
            # Obtener solicitudes antiguas
            old_requests_stmt = select(PendingChannelRequest).where(
                PendingChannelRequest.request_timestamp < cutoff_date
            )
            result = await self.session.execute(old_requests_stmt)
            old_requests = result.scalars().all()
            
            # Eliminar solicitudes antiguas
            for request in old_requests:
                await self.session.delete(request)
            
            await self.session.commit()
            
            logger.info(f"Cleaned up {len(old_requests)} old channel requests")
            return len(old_requests)
            
        except Exception as e:
            logger.error(f"Error cleaning up old requests: {e}")
            return 0
