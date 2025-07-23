"""
Handlers para administración del canal gratuito.
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from services.free_channel_service import FreeChannelService
from services.config_service import ConfigService
from keyboards.inline_post_kb import get_reaction_kb
from keyboards.free_channel_admin_kb import (
    get_free_channel_admin_kb,
    get_wait_time_selection_kb,
    get_channel_post_options_kb,
    get_content_protection_kb
)

router = Router()


class FreeChannelStates(StatesGroup):
    """Estados para configuración del canal gratuito."""
    waiting_for_channel_id = State()
    waiting_for_wait_time = State()
    waiting_for_post_text = State()
    waiting_for_media_files = State()
    confirming_post = State()


@router.callback_query(F.data == "admin_free_channel")
async def free_channel_admin_menu(callback: CallbackQuery, session: AsyncSession):
    """Menú principal de administración del canal gratuito."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    free_service = FreeChannelService(session, callback.bot)
    stats = await free_service.get_channel_statistics()
    
    if stats["channel_configured"]:
        status_text = f"✅ **Canal Configurado**\n"
        status_text += f"📋 **ID**: `{stats['channel_id']}`\n"
        if stats.get("channel_title"):
            status_text += f"📢 **Título**: {stats['channel_title']}\n"
        if stats.get("channel_member_count"):
            status_text += f"👥 **Miembros**: {stats['channel_member_count']}\n"
        status_text += f"⏰ **Tiempo de espera**: {stats['wait_time_minutes']} minutos\n"
        status_text += f"📋 **Solicitudes pendientes**: {stats['pending_requests']}\n"
        status_text += f"✅ **Total procesadas**: {stats['total_processed']}"
    else:
        status_text = "❌ **Canal no configurado**\n\nConfigura tu canal gratuito para comenzar."
    
    text = f"🆓 **Administración Canal Gratuito**\n\n{status_text}"
    
    await menu_manager.update_menu(
        callback,
        text,
        get_free_channel_admin_kb(stats["channel_configured"]),
        session,
        "admin_free_channel"
    )
    await callback.answer()


@router.callback_query(F.data == "configure_free_channel")
async def configure_free_channel(callback: CallbackQuery, state: FSMContext):
    """Iniciar configuración del canal gratuito."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await callback.message.edit_text(
        "🆓 **Configurar Canal Gratuito**\n\n"
        "Para configurar tu canal gratuito, reenvía cualquier mensaje del canal aquí.\n"
        "El bot detectará automáticamente el ID del canal.\n\n"
        "**Importante**: Asegúrate de que el bot sea administrador del canal "
        "con permisos para aprobar solicitudes de unión.",
        reply_markup=get_free_channel_admin_kb(False)
    )
    
    await state.set_state(FreeChannelStates.waiting_for_channel_id)
    await callback.answer()


@router.message(FreeChannelStates.waiting_for_channel_id)
async def process_free_channel_id(message: Message, state: FSMContext, session: AsyncSession):
    """Procesar ID del canal gratuito."""
    if not await is_admin(message.from_user.id, session):
        return
    
    channel_id = None
    channel_title = None
    
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
    else:
        try:
            channel_id = int(message.text.strip())
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return
    
    # Configurar el canal
    free_service = FreeChannelService(session, message.bot)
    success = await free_service.set_free_channel_id(channel_id)
    
    if success:
        title_text = f" ({channel_title})" if channel_title else ""
        await menu_manager.show_menu(
            message,
            f"✅ **Canal Gratuito Configurado**\n\n"
            f"**ID del Canal**: `{channel_id}`{title_text}\n\n"
            f"El canal ha sido configurado exitosamente. Los usuarios podrán "
            f"solicitar unirse y serán aprobados automáticamente según el tiempo de espera configurado.",
            get_free_channel_admin_kb(True),
            session,
            "admin_free_channel"
        )
    else:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error de Configuración**\n\nNo se pudo configurar el canal. Intenta nuevamente.",
            auto_delete_seconds=5
        )
    
    await state.clear()


@router.callback_query(F.data == "set_wait_time")
async def set_wait_time_menu(callback: CallbackQuery, session: AsyncSession):
    """Menú para configurar tiempo de espera."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    free_service = FreeChannelService(session, callback.bot)
    current_wait = await free_service.get_wait_time_minutes()
    
    await callback.message.edit_text(
        f"⏰ **Configurar Tiempo de Espera**\n\n"
        f"**Tiempo actual**: {current_wait} minutos\n\n"
        f"Selecciona el nuevo tiempo de espera para aprobar automáticamente "
        f"las solicitudes de unión al canal gratuito:",
        reply_markup=get_wait_time_selection_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wait_time_"))
async def set_wait_time_value(callback: CallbackQuery, session: AsyncSession):
    """Establecer tiempo de espera específico."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    minutes = int(callback.data.split("_")[-1])
    
    free_service = FreeChannelService(session, callback.bot)
    success = await free_service.set_wait_time_minutes(minutes)
    
    if success:
        if minutes == 0:
            time_text = "inmediatamente"
        elif minutes < 60:
            time_text = f"{minutes} minutos"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes > 0:
                time_text = f"{hours} horas y {remaining_minutes} minutos"
            else:
                time_text = f"{hours} horas"
        
        await callback.answer(f"✅ Tiempo configurado: {time_text}", show_alert=True)
        await free_channel_admin_menu(callback, session)
    else:
        await callback.answer("❌ Error al configurar el tiempo", show_alert=True)


@router.callback_query(F.data == "create_invite_link")
async def create_invite_link(callback: CallbackQuery, session: AsyncSession):
    """Crear enlace de invitación para el canal gratuito."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    free_service = FreeChannelService(session, callback.bot)
    invite_link = await free_service.create_invite_link(
        expire_hours=168,  # 7 días
        creates_join_request=True
    )
    
    if invite_link:
        await callback.message.edit_text(
            f"🔗 **Enlace de Invitación Creado**\n\n"
            f"**Enlace**: `{invite_link}`\n\n"
            f"📋 **Características**:\n"
            f"• Expira en 7 días\n"
            f"• Requiere aprobación (solicitud de unión)\n"
            f"• Los usuarios serán aprobados automáticamente según el tiempo configurado\n\n"
            f"Comparte este enlace para que los usuarios puedan solicitar unirse al canal gratuito.",
            reply_markup=get_free_channel_admin_kb(True)
        )
    else:
        await callback.answer("❌ Error al crear el enlace", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "send_to_free_channel")
async def send_to_free_channel_menu(callback: CallbackQuery, state: FSMContext):
    """Menú para enviar contenido al canal gratuito."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await callback.message.edit_text(
        "📝 **Enviar Contenido al Canal Gratuito**\n\n"
        "Envía el texto que deseas publicar en el canal gratuito.\n"
        "Después podrás agregar multimedia y configurar la protección del contenido.",
        reply_markup=get_free_channel_admin_kb(True)
    )
    
    await state.set_state(FreeChannelStates.waiting_for_post_text)
    await callback.answer()


@router.message(FreeChannelStates.waiting_for_post_text)
async def process_post_text(message: Message, state: FSMContext):
    """Procesar texto del post."""
    if not await is_admin(message.from_user.id, session):
        return
    
    await state.update_data(post_text=message.text)
    
    await message.answer(
        f"📝 **Texto del Post**\n\n{message.text}\n\n"
        f"¿Deseas agregar archivos multimedia (fotos, videos, documentos)?",
        reply_markup=get_channel_post_options_kb()
    )
    
    await state.set_state(FreeChannelStates.waiting_for_media_files)


@router.callback_query(FreeChannelStates.waiting_for_media_files, F.data == "add_media")
async def add_media_prompt(callback: CallbackQuery):
    """Solicitar archivos multimedia."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await callback.message.edit_text(
        "📎 **Agregar Multimedia**\n\n"
        "Envía los archivos que deseas incluir (fotos, videos, documentos, audio).\n"
        "Puedes enviar múltiples archivos.\n\n"
        "Cuando termines, usa el botón 'Continuar sin multimedia' para proceder.",
        reply_markup=get_channel_post_options_kb()
    )
    await callback.answer()


@router.message(FreeChannelStates.waiting_for_media_files)
async def process_media_files(message: Message, state: FSMContext):
    """Procesar archivos multimedia."""
    if not await is_admin(message.from_user.id, session):
        return
    
    data = await state.get_data()
    media_files = data.get("media_files", [])
    
    # Procesar diferentes tipos de multimedia
    if message.photo:
        media_files.append({
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "caption": message.caption
        })
    elif message.video:
        media_files.append({
            "type": "video", 
            "file_id": message.video.file_id,
            "caption": message.caption
        })
    elif message.document:
        media_files.append({
            "type": "document",
            "file_id": message.document.file_id,
            "caption": message.caption
        })
    elif message.audio:
        media_files.append({
            "type": "audio",
            "file_id": message.audio.file_id,
            "caption": message.caption
        })
    
    await state.update_data(media_files=media_files)
    
    await message.answer(
        f"📎 **Archivos agregados**: {len(media_files)}\n\n"
        f"Puedes enviar más archivos o continuar con la configuración.",
        reply_markup=get_channel_post_options_kb()
    )


@router.callback_query(FreeChannelStates.waiting_for_media_files, F.data == "continue_without_media")
async def continue_without_media(callback: CallbackQuery, state: FSMContext):
    """Continuar sin multimedia."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    media_count = len(data.get("media_files", []))
    
    await callback.message.edit_text(
        f"🔒 **Configurar Protección del Contenido**\n\n"
        f"📝 **Texto**: {data.get('post_text', 'Sin texto')[:100]}...\n"
        f"📎 **Archivos multimedia**: {media_count}\n\n"
        f"¿Deseas proteger el contenido? (Los usuarios no podrán reenviarlo o copiarlo)",
        reply_markup=get_content_protection_kb()
    )
    
    await state.set_state(FreeChannelStates.confirming_post)
    await callback.answer()


@router.callback_query(FreeChannelStates.confirming_post, F.data.startswith("protect_"))
async def confirm_and_send_post(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirmar y enviar el post al canal."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    protect_content = callback.data == "protect_yes"
    data = await state.get_data()
    
    free_service = FreeChannelService(session, callback.bot)
    
    config = ConfigService(session)
    buttons = await config.get_reaction_buttons()
    channel_id = await config.get_free_channel_id()
    sent_message = await free_service.send_message_to_channel(
        text=data.get("post_text", ""),
        protect_content=protect_content,
        reply_markup=get_reaction_kb(
            reactions=buttons,
            current_counts={},
            message_id=0,
            channel_id=channel_id or 0,
        ),
        media_files=data.get("media_files", [])
    )

    if sent_message:
        channel_id = await config.get_free_channel_id()
        await callback.bot.edit_message_reply_markup(
            chat_id=channel_id,
            message_id=sent_message.message_id,
            reply_markup=get_reaction_kb(
                reactions=buttons,
                current_counts={},
                message_id=sent_message.message_id,
                channel_id=channel_id or 0,
            ),
        )
    
    if sent_message:
        protection_text = "con protección" if protect_content else "sin protección"
        media_count = len(data.get("media_files", []))
        
        await callback.message.edit_text(
            f"✅ **Contenido Publicado**\n\n"
            f"El contenido ha sido enviado al canal gratuito {protection_text}.\n\n"
            f"📝 **ID del mensaje**: {sent_message.message_id}\n"
            f"📎 **Archivos incluidos**: {media_count}",
            reply_markup=get_free_channel_admin_kb(True)
        )
    else:
        await callback.message.edit_text(
            f"❌ **Error al Publicar**\n\n"
            f"No se pudo enviar el contenido al canal. Verifica que el bot "
            f"tenga permisos de administrador en el canal.",
            reply_markup=get_free_channel_admin_kb(True)
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "process_pending_now")
async def process_pending_now(callback: CallbackQuery, session: AsyncSession):
    """Procesar solicitudes pendientes manualmente."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    free_service = FreeChannelService(session, callback.bot)
    processed_count = await free_service.process_pending_requests()
    
    await callback.answer(
        f"✅ Procesadas {processed_count} solicitudes pendientes",
        show_alert=True
    )
    
    # Actualizar el menú con las nuevas estadísticas
    await free_channel_admin_menu(callback, session)


@router.callback_query(F.data == "cleanup_old_requests")
async def cleanup_old_requests(callback: CallbackQuery, session: AsyncSession):
    """Limpiar solicitudes antiguas."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    free_service = FreeChannelService(session, callback.bot)
    cleaned_count = await free_service.cleanup_old_requests(days_old=30)
    
    await callback.answer(
        f"🧹 Limpiadas {cleaned_count} solicitudes antiguas",
        show_alert=True
    )
    
    # Actualizar el menú
    await free_channel_admin_menu(callback, session)
