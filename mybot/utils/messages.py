# utils/messages.py
"""Centralized texts for the bot."""

# Messages from the Butler of the Divan
BUTLER_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Bienvenid@ a *El Diván de Diana*…\n\n"
        "Permítame presentarle las maravillas de este lugar. Cada gesto y decisión cuenta en *El Juego del Diván*.\n\n"
        "¿List@ para descubrir lo que le espera? Elija por dónde comenzar y yo me encargaré de guiarle con la debida cortesía."
    ),
    "start_welcome_returning_user": (
        "✨ Me alegra tenerle de regreso.\n\n"
        "Su lugar permanece reservado y sus puntos también. Hay nuevas sorpresas aguardando.\n\n"
        "¿Desea continuar su travesía en *El Juego del Diván*?"
    ),
    "vip_activation_details": (
        "Su membresía VIP ha sido activada por {duration} días.\n"
        "Expira el: {expires_at}.\n\n"
        "Si lo desea, puede unirse a nuestro canal VIP con el enlace a continuación:\n{invite_link}\n\n"
        "Este enlace es personal y expirará en 24 horas."
    ),
    "vip_activation_no_link": (
        "Su membresía VIP ha sido activada por {duration} días.\n"
        "Expira el: {expires_at}.\n\n"
        "Use /vip_menu para acceder a sus beneficios VIP."
    ),
    "vip_members_only": "Esta sección está disponible solo para miembros VIP.",
    "profile_not_registered": "Parece que aún no ha iniciado su recorrido. Use /start para dar su primer paso.",
    "profile_title": "🛋️ *Su rincón en El Diván de Diana*",
    "profile_points": "📌 *Puntos acumulados:* `{user_points}`",
    "profile_level": "🎯 *Nivel actual:* `{user_level}`",
    "profile_points_to_next_level": "📶 *Para el siguiente nivel:* `{points_needed}` más (Nivel `{next_level}` a partir de `{next_level_threshold}`)",
    "profile_max_level": "🌟 Ha alcanzado el nivel más alto. Mis felicitaciones.",
    "profile_achievements_title": "🏅 *Logros desbloqueados*",
    "profile_no_achievements": "Aún no hay logros, pero confío en que los obtendrá.",
    "profile_active_missions_title": "📋 *Sus desafíos activos*",
    "profile_no_active_missions": "Por ahora no hay desafíos disponibles, pero pronto habrá novedades.",
    "ranking_title": "🏆 *Tabla de Posiciones*",
    "ranking_entry": "#{rank}. @{username} - Puntos: `{points}`, Nivel: `{level}`",
    "no_ranking_data": "Aún no hay datos en el ranking. Sea usted el primero en aparecer.",
    "no_active_subscription": "No tiene una suscripción activa.",
}

# Messages from Señorita Kinky
KINKY_MESSAGES = {
    "vip_welcome_special": (
        "Hola, mi Kinky. Qué emoción que estés aquí, donde todo lo especial sucede. "
        "Prepárate, porque este será nuestro rincón secreto. Desde ahora te dejo a cargo de mi querido Mayordomo del Diván, "
        "él cuidará de ti y te llevará de la mano. Pero no te preocupes… seguiré muy, muy cerca."
    ),
    "verify_instagram": "📡 Verificando Instagram...",
    "reconnecting": "🔄 Reintentando conexión...",
    "verified": "✅ ¡Perfecto! Instagram verificado.",
    "gift_unlocked": "✨ ¡Regalo desbloqueado! Aquí tienes una sorpresa para ti solo: [contenido de muestra o enlace al pack gratuito]",
    "PACK_INTEREST_REPLY": "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky ",
}

# Menu texts and general options
MENU_TEXTS = {
    "FREE_MENU_TEXT": "✨ *Bienvenid@ a mi espacio gratuito*\n\nElige y descubre un poco de mi mundo...",
    "FREE_GIFT_TEXT": "🎁 *Desbloquear regalo*\nActiva tu obsequio de bienvenida y descubre los primeros detalles de todo lo que tengo para ti.",
    "PACKS_MENU_TEXT": (
        "🎀 *Paquetes especiales de Diana* 🎀\n\n"
        "¿Quieres una probadita de mis momentos más intensos?\n\n"
        "Estos son sets que puedes comprar directamente, sin suscripción. Cada uno incluye fotos y videos explícitos. 🥵\n\n"
        "🛍️ Elige tu favorito y presiona *“Me interesa”*. Yo me pondré en contacto contigo."
    ),
    "FREE_VIP_EXPLORE_TEXT": (
        "🔐 *Bienvenido al Diván de Diana* 🔐\n\n"
        "¿Te atreves a entrar a mi universo sin censura?\n\n"
        "✨ Más de 2000 archivos privados\n"
        "🎬 Videos explícitos sin censura\n"
        "🎁 Descuentos en contenido personalizado\n"
        "👀 Acceso exclusivo a mis historias diarias\n\n"
        "📌 Precio: *$350 MXN / mes*"
    ),
    "VIP_INTEREST_REPLY": (
        "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. "
        "O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky "
    ),
    "FREE_CUSTOM_TEXT": "💌 *Quiero contenido personalizado*\nCuéntame tus fantasías y recibirás algo hecho solo para ti.",
    "FREE_GAME_TEXT": "🎮 *Modo gratuito del juego Kinky*\nDisfruta de un adelanto de la diversión. La versión completa te espera en el VIP.",
    "FREE_FOLLOW_TEXT": "🌐 *¿Dónde más seguirme?*\nEncuentra todos mis enlaces y redes para que no te pierdas nada.",
    "PACK_1_DETAILS": (
        "💫 *Encanto Inicial*\n"
        "Una primera mirada. Una chispa.\n"
        "Aquí comienza el juego entre tú y yo…\n\n"
        "Este set es tu puerta de entrada a mi mundo:\n"
        "📹 1 video íntimo donde mis dedos exploran lentamente mientras mis labios y mirada te envuelven.\n"
        "📸 10 fotos donde apenas cubro lo necesario… lencería suave, piel desnuda, miradas insinuantes.\n\n"
        "Perfecto si quieres conocerme de una forma dulce, coqueta y provocadora.\n\n"
        "*150 MXN (10 USD)*"
    ),
    "PACK_2_DETAILS": (
        "🔥 *Sensualidad Revelada*\n"
        "Te muestro más. Te invito a quedarte…\n\n"
        "Este set revela lo que solo pocos han visto:\n"
        "📹 2 videos donde me toco sin censura, jugando con mi cuerpo mientras mi rostro refleja cada sensación.\n"
        "📸 10 fotos tan provocadoras que te harán dudar si mirar una sola vez será suficiente.\n\n"
        "Es mi manera de decirte:\n"
        "“No es lo que ves... es cómo te lo muestro.”\n\n"
        "*200 MXN (14 USD)*"
    ),
    "PACK_3_DETAILS": (
        "💋 *Pasión Desbordante*\n"
        "Aquí ya no hay timidez. Solo deseo.\n\n"
        "Este set está hecho para quienes quieren ver *todo* lo que puedo provocar:\n"
        "📹 3 videos:\n"
        "1. En lencería de alto voltaje\n"
        "2. Vestida, pero seduciéndote con juegos visuales\n"
        "3. Jugando con un juguetito que me hace gemir suave… y fuerte.\n"
        "📸 15 fotos íntimas y provocativas, capturadas en el punto exacto entre arte y placer.\n\n"
        "Un set para perderte y volver a verme... muchas veces.\n\n"
        "*250 MXN (17 USD)*"
    ),
    "PACK_4_DETAILS": (
        "🔞 *Intimidad Explosiva*\n\n"
        "Esto no es un set. Es una confesión explícita…\n\n"
        "Mi lado más sucio, más real, más entregado:\n"
        "📹 5 videos:\n"
        "- Me masturbo hasta acabar... sin cortes.\n"
        "- Uso dildos, me abro, gimo, me muerdo los labios.\n"
        "- Me desvisto lentamente hasta estar completamente desnuda.\n"
        "- Juego con mis juguetes favoritos.\n"
        "- Y uno… donde estoy montando, moviéndome como si estuvieras debajo. Sin censura.\n\n"
        "📸 15 fotos extra, como regalo. Fotos que no circulan por ningún otro lado.\n\n"
        "Este es el set que convierte la fantasía en algo real.\n"
        "Lo más explícito. Lo más mío. Lo más tuyo.\n\n"
        "*300 MXN (20 USD)*"
    ),
}

# Mission and minigame messages
MISSION_MESSAGES = {
    "missions_title": "🎯 *Desafíos disponibles*",
    "missions_no_active": "No hay desafíos por el momento. Aproveche para tomar aliento.",
    "mission_not_found": "Ese desafío no existe o ya expiró.",
    "mission_already_completed": "Ya lo completó. Excelente trabajo.",
    "mission_completed_success": "✅ ¡Desafío completado! Ganó `{points_reward}` puntos.",
    "mission_completed_feedback": "🎉 ¡Misión '{mission_name}' completada! Ganó `{points_reward}` puntos.",
    "mission_level_up_bonus": "🚀 Ha subido de nivel. Ahora está en el nivel `{user_level}`. Las aventuras serán más emocionantes.",
    "mission_achievement_unlocked": "\n🏆 Logro desbloqueado: *{achievement_name}*",
    "mission_completion_failed": "❌ No pudimos registrar este desafío. Verifique si ya lo completó antes o si aún está activo.",
    "reward_shop_title": "🎁 *Recompensas del Diván*",
    "reward_shop_empty": "Por ahora no hay recompensas disponibles. Pero pronto sí.",
    "reward_not_found": "Esa recompensa ya no está disponible.",
    "reward_not_registered": "Su perfil no está activo. Use /start para comenzar *El Juego del Diván*.",
    "reward_not_enough_points": "Le faltan `{required_points}` puntos. Actualmente tiene `{user_points}`.",
    "reward_claim_success": "🎉 ¡Recompensa reclamada!",
    "reward_claim_failed": "No pudimos procesar su solicitud.",
    "reward_already_claimed": "Esta recompensa ya fue reclamada.",
    "level_up_notification": "🎉 ¡Subió a Nivel {level}: {level_name}! {reward}",
    "special_level_reward": "✨ Recompensa especial por alcanzar el nivel {level}! {reward}",
    "menu_missions_text": "Aquí están los desafíos que puede emprender. ¡Cada uno le acerca más!",
    "menu_rewards_text": "¡Es momento de canjear sus puntos! Estas son las recompensas disponibles:",
    "confirm_purchase_message": "¿Está segur@ de que desea canjear {reward_name} por {reward_cost} puntos?",
    "purchase_cancelled_message": "Compra cancelada. Puede seguir explorando otras recompensas.",
    "gain_points_instructions": "Puede ganar puntos completando misiones y participando en las actividades del canal.",
    "points_total_notification": "Ahora tiene {total_points} puntos acumulados.",
    "checkin_success": "✅ Check-in registrado. Ganó {points} puntos.",
    "checkin_already_done": "Ya realizó su check-in. Vuelva mañana.",
    "daily_gift_received": "🎁 Recibió {points} puntos del regalo diario!",
    "daily_gift_already": "Ya reclamó el regalo diario. Vuelva mañana.",
    "daily_gift_disabled": "Regalos diarios deshabilitados.",
    "minigames_disabled": "Minijuegos deshabilitados.",
    "dice_points": "Ganó {points} puntos lanzando el dado.",
    "trivia_correct": "¡Correcto! +5 puntos",
    "trivia_wrong": "Respuesta incorrecta.",
    "reaction_registered_points": "✅ Reacci\u00f3n registrada. Ganaste {points} puntos.",
    "reaction_already": "Ya has reaccionado a este post.",
    "weekly_ranking_title": "🏅 Ranking Semanal de Reacciones",
    "weekly_ranking_entry": "#{rank}. @{username} - {count} reacciones",
    "challenge_started": "Reto iniciado! Reacciona a {count} publicaciones para ganar puntos.",
    "mission_details_text": (
        "🎯 *{mission_name}*\n"
        "{mission_description}\n\n"
        "🏆 Recompensa: {points_reward} puntos\n"
        "🗂 Tipo: {mission_type}"
    ),
    "view_all_missions_button_text": "📋 Ver Todas las Misiones",
}

# Aggregate all messages for backward compatibility
BOT_MESSAGES = {
    **BUTLER_MESSAGES,
    **KINKY_MESSAGES,
    **MENU_TEXTS,
    **MISSION_MESSAGES,
}

# Badge descriptions
BADGE_TEXTS = {
    "first_message": {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
    },
    "conversador": {
        "name": "Conversador",
        "description": "Alcanza 100 mensajes enviados",
    },
    "invitador": {
        "name": "Invitador",
        "description": "Consigue 5 invitaciones exitosas",
    },
}

NIVEL_TEMPLATE = """
🎮 Tu nivel actual: {current_level}
✨ Puntos totales: {points}
📊 Progreso hacia el siguiente nivel: {percentage:.1%}
🎯 Te faltan {points_needed} puntos para alcanzar el nivel {next_level}.
"""
TRIVIA_INTRO_MESSAGE = "🎲 *Selecciona una trivia:*"
TRIVIA_COMPLETE_MESSAGE = "🎉 *Has completado la trivia con {score} respuestas correctas.*"
TRIVIA_ADMIN_MENU = "🛠️ *Panel de Administración de Trivias*"
