"""
Multi-tenant service for managing independent bot configurations.
Allows multiple users to set up their own bot instances with separate channels and settings.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import ConfigEntry, User, Tariff
from services.config_service import ConfigService
from services.channel_service import ChannelService
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)

class TenantService:
    """
    Service for managing multi-tenant bot configurations.
    Each admin can configure their own channels, tariffs, and settings.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_service = ConfigService(session)
        self.channel_service = ChannelService(session)
    
    async def initialize_tenant(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Initialize a new tenant configuration for an admin user.
        
        Returns:
            Dict with initialization status and next steps
        """
        try:
            # Ensure user exists and is marked as admin
            user = await self.session.get(User, admin_user_id)
            if not user:
                user = User(id=admin_user_id, role="admin")
                self.session.add(user)
            else:
                user.role = "admin"
            
            await self.session.commit()
            
            # Check if tenant is already configured
            config_status = await self.get_tenant_status(admin_user_id)
            
            logger.info(f"Initialized tenant for admin {admin_user_id}")
            return {
                "success": True,
                "user_id": admin_user_id,
                "status": config_status,
                "next_steps": self._get_next_steps(config_status)
            }
            
        except Exception as e:
            logger.error(f"Error initializing tenant for {admin_user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_tenant_status(self, admin_user_id: int) -> Dict[str, bool]:
        """
        Get the configuration status for a tenant.
        
        Returns:
            Dict with boolean flags for each configuration aspect
        """
        try:
            # Check channel configuration
            vip_channel = await self.config_service.get_vip_channel_id()
            free_channel = await self.config_service.get_free_channel_id()
            
            # Check tariff configuration
            stmt = select(Tariff)
            result = await self.session.execute(stmt)
            tariffs = result.scalars().all()
            
            # Check gamification setup (basic missions, levels, etc.)
            from services.mission_service import MissionService
            from services.level_service import LevelService
            
            mission_service = MissionService(self.session)
            level_service = LevelService(self.session)
            
            missions = await mission_service.get_active_missions()
            levels = await level_service.list_levels()
            
            return {
                "channels_configured": bool(vip_channel or free_channel),
                "vip_channel_configured": bool(vip_channel),
                "free_channel_configured": bool(free_channel),
                "tariffs_configured": len(tariffs) > 0,
                "gamification_configured": len(missions) > 0 and len(levels) > 0,
                "basic_setup_complete": bool(vip_channel or free_channel) and len(tariffs) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting tenant status for {admin_user_id}: {e}")
            return {
                "channels_configured": False,
                "vip_channel_configured": False,
                "free_channel_configured": False,
                "tariffs_configured": False,
                "gamification_configured": False,
                "basic_setup_complete": False
            }
    
    async def configure_channels(
        self, 
        admin_user_id: int, 
        vip_channel_id: Optional[int] = None,
        free_channel_id: Optional[int] = None,
        channel_titles: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Configure channels for a tenant.
        
        Args:
            admin_user_id: The admin user configuring the channels
            vip_channel_id: Optional VIP channel ID
            free_channel_id: Optional free channel ID
            channel_titles: Optional dict with channel titles
        
        Returns:
            Dict with configuration result
        """
        try:
            results = {}
            
            if vip_channel_id:
                await self.config_service.set_vip_channel_id(vip_channel_id)
                title = channel_titles.get("vip") if channel_titles else None
                await self.channel_service.add_channel(vip_channel_id, title)
                results["vip_configured"] = True
                logger.info(f"VIP channel {vip_channel_id} configured for admin {admin_user_id}")
            
            if free_channel_id:
                await self.config_service.set_free_channel_id(free_channel_id)
                title = channel_titles.get("free") if channel_titles else None
                await self.channel_service.add_channel(free_channel_id, title)
                results["free_configured"] = True
                logger.info(f"Free channel {free_channel_id} configured for admin {admin_user_id}")
            
            # Set tenant as configured
            await self.config_service.set_value(f"tenant_{admin_user_id}_channels_setup", "true")
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error configuring channels for admin {admin_user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def setup_default_gamification(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Set up default gamification elements for a new tenant.
        
        Returns:
            Dict with setup results
        """
        try:
            from services.mission_service import MissionService
            from services.level_service import LevelService
            from services.achievement_service import AchievementService
            
            mission_service = MissionService(self.session)
            level_service = LevelService(self.session)
            achievement_service = AchievementService(self.session)
            
            # Initialize default levels
            await level_service._init_levels()
            
            # Initialize default achievements
            await achievement_service.ensure_achievements_exist()
            
            # Create default missions
            default_missions = [
                {
                    "name": "Primer Mensaje",
                    "description": "Envía tu primer mensaje en el chat",
                    "mission_type": "messages",
                    "target_value": 1,
                    "reward_points": 10,
                    "duration_days": 0
                },
                {
                    "name": "Check-in Diario",
                    "description": "Realiza tu check-in diario con /checkin",
                    "mission_type": "daily",
                    "target_value": 1,
                    "reward_points": 5,
                    "duration_days": 1
                },
                {
                    "name": "Conversador Activo",
                    "description": "Envía 10 mensajes en el chat",
                    "mission_type": "messages",
                    "target_value": 10,
                    "reward_points": 25,
                    "duration_days": 0
                }
            ]
            
            created_missions = []
            for mission_data in default_missions:
                mission = await mission_service.create_mission(
                    mission_data["name"],
                    mission_data["description"],
                    mission_data["mission_type"],
                    mission_data["target_value"],
                    mission_data["reward_points"],
                    mission_data["duration_days"]
                )
                created_missions.append(mission.name)
            
            # Mark gamification as configured
            await self.config_service.set_value(f"tenant_{admin_user_id}_gamification_setup", "true")
            
            logger.info(f"Default gamification setup completed for admin {admin_user_id}")
            return {
                "success": True,
                "missions_created": created_missions,
                "levels_initialized": True,
                "achievements_initialized": True
            }
            
        except Exception as e:
            logger.error(f"Error setting up gamification for admin {admin_user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_default_tariffs(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Create default VIP tariffs for a new tenant.
        
        Returns:
            Dict with created tariffs
        """
        try:
            default_tariffs = [
                {"name": "VIP Básico", "duration_days": 30, "price": 10},
                {"name": "VIP Premium", "duration_days": 90, "price": 25},
                {"name": "VIP Anual", "duration_days": 365, "price": 100}
            ]
            
            created_tariffs = []
            for tariff_data in default_tariffs:
                tariff = Tariff(
                    name=tariff_data["name"],
                    duration_days=tariff_data["duration_days"],
                    price=tariff_data["price"]
                )
                self.session.add(tariff)
                created_tariffs.append(tariff_data["name"])
            
            await self.session.commit()
            
            # Mark tariffs as configured
            await self.config_service.set_value(f"tenant_{admin_user_id}_tariffs_setup", "true")
            
            logger.info(f"Default tariffs created for admin {admin_user_id}")
            return {
                "success": True,
                "tariffs_created": created_tariffs
            }
            
        except Exception as e:
            logger.error(f"Error creating default tariffs for admin {admin_user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_next_steps(self, config_status: Dict[str, bool]) -> list:
        """
        Determine the next configuration steps based on current status.
        
        Returns:
            List of recommended next steps
        """
        steps = []
        
        if not config_status["channels_configured"]:
            steps.append("configure_channels")
        
        if not config_status["tariffs_configured"]:
            steps.append("setup_tariffs")
        
        if not config_status["gamification_configured"]:
            steps.append("setup_gamification")
        
        if not steps:
            steps.append("configuration_complete")
        
        return steps
    
    async def get_tenant_summary(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the tenant's configuration.
        
        Returns:
            Dict with complete tenant information
        """
        try:
            status = await self.get_tenant_status(admin_user_id)
            
            # Get channel information
            vip_channel_id = await self.config_service.get_vip_channel_id()
            free_channel_id = await self.config_service.get_free_channel_id()
            
            # Get tariff count
            stmt = select(Tariff)
            result = await self.session.execute(stmt)
            tariff_count = len(result.scalars().all())
            
            # Get user count
            from sqlalchemy import func
            user_count_stmt = select(func.count()).select_from(User)
            user_count_result = await self.session.execute(user_count_stmt)
            total_users = user_count_result.scalar() or 0
            
            return {
                "admin_user_id": admin_user_id,
                "configuration_status": status,
                "channels": {
                    "vip_channel_id": vip_channel_id,
                    "free_channel_id": free_channel_id
                },
                "tariff_count": tariff_count,
                "total_users": total_users,
                "setup_complete": status["basic_setup_complete"]
            }
            
        except Exception as e:
            logger.error(f"Error getting tenant summary for {admin_user_id}: {e}")
            return {
                "admin_user_id": admin_user_id,
                "error": str(e)
            }
