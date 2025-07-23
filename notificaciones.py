import random
from aiogram import Bot

lucien_mensajes = [
    "Sabías que los flamencos pueden dormir mientras están de pie? Lucien aprueba.",
    "Lucien dice: No te fíes de los patos, ellos siempre están tramando algo.",
    "Hoy es un gran día para acumular pistas, o para no hacer nada. Tú decides.",
    "Cada reacción cuenta, incluso la tuya, humano.",
    "Lucien quiere saber: ¿cuántos besitos has coleccionado hoy?",
    "Datos absurdos: Las vacas pueden subir escaleras pero no bajarlas.",
    "Lucien dice: Sigue reaccionando, el Diván te observa.",
    "A veces un besito abre más puertas que mil llaves.",
    "Lucien aprobó tu reacción con su sello de sarcasmo.",
    "¿Ya tomaste agua? Lucien está pendiente de ti."
]

user_last_message = {}

async def enviar_notificacion_gamificada(bot: Bot, user_id: int):
    mensaje = random.choice(lucien_mensajes)

    while user_last_message.get(user_id) == mensaje and len(lucien_mensajes) > 1:
        mensaje = random.choice(lucien_mensajes)

    user_last_message[user_id] = mensaje
    await bot.send_message(user_id, f"💬 {mensaje}")


async def send_narrative_notification(bot: Bot, user_id: int, pista_code: str, origen: str = "Sistema"):
    mensajes = [
        f"🎩 Lucien: Una nueva pieza ha caído en tus manos... {pista_code}. No la pierdas.",
        f"🎩 Lucien: {pista_code} se ha revelado para ti. ¿Podrás entender su verdadero valor?",
        f"🎩 Lucien: Has desbloqueado algo nuevo. {pista_code}... interesante.",
        f"🎩 Lucien: El Diván susurra: {pista_code} es ahora tuyo.",
        f"🎩 Lucien: {pista_code} proviene de {origen}. ¿Accidente o destino?"
    ]

    mensaje = random.choice(mensajes)
    await bot.send_message(user_id, mensaje)
