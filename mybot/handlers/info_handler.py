from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "guia_principiante")
async def show_travel_guide(callback: CallbackQuery):
    """Placeholder para la guía del viajero."""
    await callback.answer(
        "La Guía del Viajero aún está en desarrollo. ¡Pronto estará disponible!",
        show_alert=True,
    )
