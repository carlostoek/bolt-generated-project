from .admin_menu import router as admin_router
from .vip_menu import router as vip_router
from .free_menu import router as free_router
from .config_menu import router as config_router
from .channel_admin import router as channel_admin_router
from .subscription_plans import router as subscription_plans_router
from .game_admin import router as game_admin_router
from .event_admin import router as event_admin_router
from .admin_config import router as admin_config_router
from .trivia_admin import router as trivia_admin_router

# Asegúrate de incluir trivia_admin_router al registrar routers:
admin_router.include_router(trivia_admin_router)

__all__ = [
    "admin_router",
    "vip_router",
    "free_router",
    "config_router",
    "channel_admin_router",
    "subscription_plans_router",
    "game_admin_router",
    "event_admin_router",
    "admin_config_router",
]
