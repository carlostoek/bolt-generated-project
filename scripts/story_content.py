# scripts/story_content.py

"""
Este archivo contiene el storyboard completo de la narrativa inmersiva.
Está diseñado para ser fácilmente editable por guionistas y diseñadores de narrativa.

Formato de cada fragmento:
{
    "key": "IDENTIFICADOR_UNICO",
    "character": "NombreDelPersonaje",
    "text": "El texto que verá el usuario.",
    "level": 1,  # Nivel narrativo (1-3 gratis, 4-6 VIP)
    "choices": [
        {
            "text": "Texto del botón de decisión",
            "destination_key": "KEY_DEL_SIGUIENTE_FRAGMENTO"
        },
        # ... más decisiones
    ],
    # Opcional: si no hay decisiones, la historia avanza automáticamente
    "auto_next_fragment_key": "KEY_DEL_SIGUIENTE_FRAGMENTO_AUTO",
    
    # Opcional: condiciones y recompensas
    "min_besitos": 0,
    "required_role": None,  # "vip"
    "reward_besitos": 0,
    "unlocks_achievement_id": None,
}
"""

STORY_BOARD = [
    # --- Nivel 1: Introducción (Gratuito) ---
    {
        "key": "START",
        "character": "Lucien",
        "text": "Bienvenido, viajero. Soy Lucien, el mayordomo. La mansión te esperaba. Diana... ella también te esperaba. ¿Estás listo para comenzar?",
        "level": 1,
        "choices": [
            {"text": "Estoy listo.", "destination_key": "LUCIEN_INTRO_2"},
            {"text": "Necesito un momento.", "destination_key": "LUCIEN_WAIT"},
        ],
    },
    {
        "key": "LUCIEN_WAIT",
        "character": "Lucien",
        "text": "El tiempo es un lujo que no todos poseemos. Tómate el que necesites, pero no tardes. El destino no espera.",
        "level": 1,
        "auto_next_fragment_key": "START",
    },
    {
        "key": "LUCIEN_INTRO_2",
        "character": "Lucien",
        "text": "Excelente. La primera regla de esta casa es que todo tiene un precio. Tus 'besitos' son la moneda de cambio para los secretos que aquí se guardan. Gánalos, y quizás descubras lo que buscas.",
        "level": 1,
        "reward_besitos": 10,
        "choices": [
            {"text": "Entendido. ¿Qué sigue?", "destination_key": "DIANA_HINT_1"},
        ],
    },
    
    # --- Nivel 2: Primer Contacto (Gratuito) ---
    {
        "key": "DIANA_HINT_1",
        "character": "Lucien",
        "text": "Diana dejó algo para ti. Un eco de su presencia. Lo encontrarás donde la luz del día no se atreve a entrar. Para acceder, necesitarás demostrar tu valía. Completa una misión diaria.",
        "level": 2,
        "choices": [
            {"text": "Buscaré esa misión.", "destination_key": "END_FREE_LEVEL"},
        ],
    },
    {
        "key": "END_FREE_LEVEL",
        "character": "Lucien",
        "text": "Te estaré observando. No me decepciones.",
        "level": 2,
        "choices": [],
    },

    # --- Nivel 4: Profundización (VIP) ---
    {
        "key": "VIP_START",
        "character": "Diana",
        "text": "Así que has llegado hasta aquí... Lucien me ha hablado de ti. Siento tu curiosidad, tu deseo. Pero, ¿qué es lo que realmente anhelas?",
        "level": 4,
        "required_role": "vip",
        "choices": [
            {"text": "Busco respuestas.", "destination_key": "VIP_DESIRE_1"},
            {"text": "Te busco a ti.", "destination_key": "VIP_DESIRE_2"},
        ],
    },
    {
        "key": "VIP_DESIRE_1",
        "character": "Diana",
        "text": "Las respuestas son solo el principio. La verdad más profunda no se encuentra, se construye. Y requiere sacrificios.",
        "level": 4,
        "required_role": "vip",
        "choices": [],
    },
    {
        "key": "VIP_DESIRE_2",
        "character": "Diana",
        "text": "A mí... Muchos me buscan. Pocos me encuentran. Demuéstrame que eres diferente.",
        "level": 4,
        "required_role": "vip",
        "choices": [],
    },
]
