from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.filters import Command

from datetime import datetime

from utils.user_roles import get_user_role
from utils.menu_utils import send_menu, update_menu, send_temporary_reply
from utils.keyboard_utils import (
    get_back_keyboard,
    get_main_menu_keyboard,
    get_missions_keyboard,
)
from keyboards.vip_main_kb import get_vip_main_kb
from utils.messages import BOT_MESSAGES
from utils.message_utils import get_profile_message
from services.subscription_service import SubscriptionService
from services.mission_service import MissionService
from services.achievement_service import AchievementService
from database.models import User, UserBadge, set_user_menu_state
from utils.text_utils import sanitize_text

router = Router()


@router.message(Command("vip_menu"))
async def vip_menu(message: Message, session: AsyncSession):
    if await get_user_role(message.bot, message.from_user.id, session=session) != "vip":
        await send_temporary_reply(
            message,
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
        )
        return
    await send_menu(
        message,
        BOT_MESSAGES["start_welcome_returning_user"],
        get_vip_main_kb(),
        session,
        "vip_main",
    )


@router.callback_query(F.data == "vip_menu")
async def vip_menu_cb(callback: CallbackQuery, session: AsyncSession):
    """Return to the VIP main menu from callbacks."""
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return
    await update_menu(
        callback,
        BOT_MESSAGES["start_welcome_returning_user"],
        get_vip_main_kb(),
        session,
        "vip_main",
    )
    await callback.answer()


@router.callback_query(F.data == "vip_subscription")
async def vip_subscription(callback: CallbackQuery, session: AsyncSession):
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return
    sub_service = SubscriptionService(session)
    sub = await sub_service.get_subscription(callback.from_user.id)

    if not sub:
        text = BOT_MESSAGES.get("no_active_subscription")
    else:
        join_date = sub.created_at.strftime("%d/%m/%Y") if sub.created_at else "?"
        if sub.expires_at:
            expire_date = sub.expires_at.strftime("%d/%m/%Y")
            days_left = (sub.expires_at - datetime.utcnow()).days
            text = (
                f"Fecha de inicio: {join_date}\n"
                f"Fecha de término: {expire_date}\n"
                f"Días restantes: {days_left}"
            )
        else:
            text = f"Fecha de inicio: {join_date}\nSin fecha de término"

    await callback.message.edit_text(
        text, reply_markup=get_back_keyboard("vip_menu")
    )
    await callback.answer()


@router.callback_query(F.data == "vip_missions")
async def vip_missions(callback: CallbackQuery, session: AsyncSession):
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return
    user = await session.get(User, callback.from_user.id)
    mission_service = MissionService(session)
    missions = await mission_service.get_daily_active_missions(user_id=callback.from_user.id)

    if not missions:
        text = BOT_MESSAGES.get("missions_no_active")
    else:
        lines = ["*Misiones disponibles:*\n"]
        for m in missions:
            completed, _ = await mission_service.check_mission_completion_status(user, m)
            status = "¡Completada! ✅" if completed else "No completada"
            lines.append(
                f"*{m.name}*\n{m.description}\nRecompensa: {m.reward_points} puntos\nEstado: {status}\n"
            )
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=get_missions_keyboard(missions))
    await callback.answer()


@router.callback_query(F.data == "vip_badges")
async def vip_badges(callback: CallbackQuery, session: AsyncSession):
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return

    ach_service = AchievementService(session)
    badges = await ach_service.get_user_badges(callback.from_user.id)

    if not badges:
        text = BOT_MESSAGES.get(
            "user_no_badges",
            "Aún no has desbloqueado ninguna insignia. ¡Sigue participando!",
        )
    else:
        # Fetch award dates
        stmt = select(UserBadge.badge_id, UserBadge.awarded_at).where(
            UserBadge.user_id == callback.from_user.id
        )
        result = await session.execute(stmt)
        dates = {row.badge_id: row.awarded_at for row in result}

        lines = ["*Tus insignias:*\n"]
        for b in badges:
            date_str = (
                f" (obtenida el {dates[b.id].strftime('%d/%m/%Y')})"
                if b.id in dates and dates[b.id]
                else ""
            )
            line = f"{b.icon or ''} *{b.name}* - {b.description or ''}{date_str}"
            lines.append(line)
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "vip_game")
async def vip_game(callback: CallbackQuery, session: AsyncSession):
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return
    await callback.message.edit_text(
        BOT_MESSAGES["start_welcome_returning_user"],
        reply_markup=get_vip_main_kb(),
    )
    await set_user_menu_state(session, callback.from_user.id, "vip_main")
    await callback.answer()


@router.callback_query(F.data == "game_profile")
async def game_profile(callback: CallbackQuery, session: AsyncSession):
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return

    user_id = callback.from_user.id
    user: User | None = await session.get(User, user_id)
    if not user:
        user = User(
            id=user_id,
            username=sanitize_text(callback.from_user.username),
            first_name=sanitize_text(callback.from_user.first_name),
            last_name=sanitize_text(callback.from_user.last_name),
        )
        session.add(user)
        await session.commit()

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id)

    profile_message = await get_profile_message(user, active_missions, session)

    sub_service = SubscriptionService(session)
    sub = await sub_service.get_subscription(user_id)
    is_active = sub and (sub.expires_at is None or sub.expires_at > datetime.utcnow())
    vip_status = "Activo" if is_active else "Expirado"

    profile_message += f"\n\nVIP: {vip_status}"

    await callback.message.edit_text(
        profile_message, reply_markup=get_back_keyboard("vip_game")
    )
    await callback.answer()


@router.callback_query(F.data == "gain_points")
async def gain_points(callback: CallbackQuery, session: AsyncSession):
    """Show information on how to earn points in the game."""
    if await get_user_role(callback.bot, callback.from_user.id, session=session) != "vip":
        await callback.answer(
            BOT_MESSAGES.get(
                "vip_members_only",
                "Esta sección está disponible solo para miembros VIP.",
            ),
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        BOT_MESSAGES.get(
            "gain_points_instructions",
            "Participa en misiones y actividades para ganar puntos."
        ),
        reply_markup=get_back_keyboard("vip_game")
    )
    await callback.answer()
