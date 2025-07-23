from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from utils.admin_state import AdminConfigStates
from utils.config import VIP_CHANNEL_ID, FREE_CHANNEL_ID
from keyboards.admin_channel_config_kb import get_save_and_cancel_kb
from keyboards.admin_main_kb import get_admin_main_kb
from keyboards.admin_vip_channel_kb import get_admin_vip_channel_kb
from keyboards.free_channel_admin_kb import get_free_channel_admin_kb
from services.channel_service import ChannelService

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "vip_config_reactions")
async def vip_config_reactions(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await state.update_data(target_channel_id=VIP_CHANNEL_ID)
    await callback.message.edit_text(
        "Envía los emojis separados por espacios para las reacciones del canal VIP:",
        reply_markup=get_save_and_cancel_kb(),
    )
    await state.set_state(AdminConfigStates.waiting_for_reactions_input)
    await callback.answer()


@router.callback_query(F.data == "free_config_reactions")
async def free_config_reactions(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await state.update_data(target_channel_id=FREE_CHANNEL_ID)
    await callback.message.edit_text(
        "Envía los emojis separados por espacios para las reacciones del canal Free:",
        reply_markup=get_save_and_cancel_kb(),
    )
    await state.set_state(AdminConfigStates.waiting_for_reactions_input)
    await callback.answer()


@router.message(AdminConfigStates.waiting_for_reactions_input)
async def process_reactions_input(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(message, "❌ Acceso Denegado.", auto_delete_seconds=3)
        await state.clear()
        return

    input_text = (message.text or "").strip()
    if not input_text:
        await message.answer(
            "Por favor, envía los emojis separados por espacios.",
            reply_markup=get_save_and_cancel_kb(),
        )
        return

    reactions = [e for e in input_text.split() if e]
    if not reactions:
        await message.answer(
            "No se detectaron emojis válidos. Por favor, intenta de nuevo.",
            reply_markup=get_save_and_cancel_kb(),
        )
        return

    if len(reactions) > 10:
        await message.answer(
            "Has ingresado más de 10 reacciones. Por favor, ingresa un máximo de 10.",
            reply_markup=get_save_and_cancel_kb(),
        )
        return

    await state.update_data(reactions=reactions)
    await state.set_state(AdminConfigStates.waiting_for_points_input)

    points_prompt = (
        "Ahora, envía los puntos para CADA REACCIÓN, separados por espacios y en el MISMO ORDEN en que las enviaste.\n\n"
    )
    points_prompt += (
        "Ejemplo: si enviaste '👍 ❤️ 🔥' y quieres que '👍' valga 0.5, '❤️' valga 1.0 y '🔥' valga 2.0, entonces envía:\n"
    )
    points_prompt += "`0.5 1.0 2.0`"
    points_prompt += f"\n\nVas a ingresar puntos para {len(reactions)} reacciones."

    await message.answer(points_prompt, reply_markup=get_save_and_cancel_kb())


@router.message(AdminConfigStates.waiting_for_points_input)
async def process_points_input(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(message, "❌ Acceso Denegado.", auto_delete_seconds=3)
        await state.clear()
        return

    input_text = (message.text or "").strip()
    if not input_text:
        await message.answer(
            "Por favor, envía los puntos separados por espacios.",
            reply_markup=get_save_and_cancel_kb(),
        )
        return

    points_str = input_text.split()
    points: list[float] = []
    data = await state.get_data()
    reactions = data.get("reactions", [])

    if len(points_str) != len(reactions):
        await message.answer(
            f"El número de puntos ingresados ({len(points_str)}) no coincide con el número de reacciones ({len(reactions)}).\n"
            "Por favor, asegúrate de ingresar un punto para cada reacción, en el mismo orden.",
            reply_markup=get_save_and_cancel_kb(),
        )
        return

    for p_str in points_str:
        try:
            point = float(p_str)
            if point < 0:
                await message.answer(
                    "Los puntos no pueden ser negativos. Por favor, inténtalo de nuevo.",
                    reply_markup=get_save_and_cancel_kb(),
                )
                return
            points.append(point)
        except ValueError:
            await message.answer(
                f"Punto inválido '{p_str}'. Por favor, ingresa solo números (ej: 0.5 1.0).",
                reply_markup=get_save_and_cancel_kb(),
            )
            return

    await state.update_data(reaction_points=points)
    await message.answer(
        "Puntos guardados temporalmente. Pulsa '✅ Guardar' para aplicar los cambios o '❌ Cancelar' para abortar.",
        reply_markup=get_save_and_cancel_kb(),
    )


@router.callback_query(
    StateFilter(AdminConfigStates.waiting_for_reactions_input, AdminConfigStates.waiting_for_points_input),
    F.data == "cancel_config",
)
async def cancel_config_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    data = await state.get_data()
    target_channel_id = data.get("target_channel_id")

    await state.clear()

    if target_channel_id == VIP_CHANNEL_ID:
        await callback.message.edit_text(
            "Configuración de reacciones VIP cancelada.",
            reply_markup=get_admin_vip_channel_kb(),
        )
    elif target_channel_id == FREE_CHANNEL_ID:
        await callback.message.edit_text(
            "Configuración de reacciones Free cancelada.",
            reply_markup=get_free_channel_admin_kb(True),
        )
    else:
        await callback.message.edit_text(
            "Configuración cancelada. Volviendo al menú principal.",
            reply_markup=get_admin_main_kb(),
        )

    await callback.answer("Configuración cancelada.")


@router.callback_query(
    StateFilter(AdminConfigStates.waiting_for_reactions_input, AdminConfigStates.waiting_for_points_input),
    F.data == "save_reactions",
)
async def save_reaction_buttons_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    data = await state.get_data()
    reactions_list = data.get("reactions", [])
    points_list = data.get("reaction_points", [])
    target_channel_id = data.get("target_channel_id")

    if not target_channel_id:
        await callback.answer("Error: ID del canal no especificado para guardar reacciones.", show_alert=True)
        logger.error(
            f"Admin {callback.from_user.id} tried to save reactions without a target_channel_id in FSMContext."
        )
        await state.clear()
        await callback.message.edit_text(
            "Algo salió mal: No se pudo determinar el canal. Intenta de nuevo.",
            reply_markup=get_admin_main_kb(),
        )
        return

    if not reactions_list:
        await callback.answer("Debes ingresar al menos una reacción.", show_alert=True)
        return

    reaction_points_dict: dict[str, float] = {}
    if len(reactions_list) == len(points_list):
        for i, emoji in enumerate(reactions_list):
            try:
                reaction_points_dict[emoji] = float(points_list[i])
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Error al convertir punto '{points_list[i]}' a float para emoji '{emoji}': {e}. Asignando 0.5 por defecto.",
                    exc_info=True,
                )
                reaction_points_dict[emoji] = 0.5
    else:
        logger.warning(
            f"Mismatch between reactions list ({len(reactions_list)}) and points list ({len(points_list)}) for channel {target_channel_id}. Defaulting points to 0.5 for all reactions."
        )
        for emoji in reactions_list:
            reaction_points_dict[emoji] = 0.5

    channel_service = ChannelService(session)
    await channel_service.set_reactions(
        chat_id=target_channel_id,
        reactions=reactions_list,
        reaction_points=reaction_points_dict,
    )

    channel_name = "VIP" if target_channel_id == VIP_CHANNEL_ID else "Free" if target_channel_id == FREE_CHANNEL_ID else str(target_channel_id)

    await callback.message.edit_text(
        f"Botones de reacción y puntos actualizados para el canal {channel_name} (ID: `{target_channel_id}`).",
        reply_markup=get_admin_main_kb(),
    )
    await state.clear()
    await callback.answer("Configuración guardada.")
