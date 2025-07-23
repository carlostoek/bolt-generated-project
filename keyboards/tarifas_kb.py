from aiogram.utils.keyboard import InlineKeyboardBuilder


from typing import Sequence
from database.models import Tariff


def get_tarifas_kb(tariffs: Sequence[Tariff] | None = None):
    """Keyboard listing existing tariffs with management options."""
    builder = InlineKeyboardBuilder()
    if tariffs:
        for t in tariffs:
            builder.button(text=t.name, callback_data=f"tariff_{t.id}")
    builder.button(text="➕ Nueva Tarifa", callback_data="tarifa_new")
    builder.button(text="🔙 Volver", callback_data="vip_config")
    builder.adjust(1)
    return builder.as_markup()


def get_tariff_options_kb(tariff_id: int):
    """Keyboard with options for a specific tariff."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar", callback_data=f"edit_tariff_{tariff_id}")
    builder.button(text="🗑 Eliminar", callback_data=f"delete_tariff_{tariff_id}")
    builder.button(text="🔙 Volver", callback_data="config_tarifas")
    builder.adjust(1)
    return builder.as_markup()


def get_duration_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="1 Día", callback_data="plan_dur_1")
    builder.button(text="3 Días", callback_data="plan_dur_3")
    builder.button(text="1 Semana", callback_data="plan_dur_7")
    builder.button(text="2 Semanas", callback_data="plan_dur_14")
    builder.button(text="1 Mes", callback_data="plan_dur_30")
    builder.button(text="3 Meses", callback_data="plan_dur_90")
    builder.button(text="6 Meses", callback_data="plan_dur_180")
    builder.button(text="1 Año", callback_data="plan_dur_365")
    builder.button(text="🔙 Cancelar", callback_data="config_tarifas")
    builder.adjust(2)
    return builder.as_markup()


def get_plan_list_kb(plans):
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(text=plan.name, callback_data=f"plan_link_{plan.id}")
    builder.adjust(1)
    return builder.as_markup()
