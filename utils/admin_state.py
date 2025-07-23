from collections import defaultdict
from typing import Dict, List

from aiogram.fsm.state import State, StatesGroup

# Simple in-memory stack of admin menu states per user
_user_states: Dict[int, List[str]] = defaultdict(list)


def reset_state(user_id: int) -> None:
    """Initialize the state stack for an admin user."""
    _user_states[user_id] = ["main"]


def push_state(user_id: int, state: str) -> None:
    """Push a new state onto the user's stack if it isn't the current one."""
    stack = _user_states.setdefault(user_id, ["main"])
    if not stack or stack[-1] != state:
        stack.append(state)


def pop_state(user_id: int) -> str:
    """Pop the current state and return the new one."""
    stack = _user_states.get(user_id, ["main"])
    if stack:
        stack.pop()
    if not stack:
        stack.append("main")
    return stack[-1]


def current_state(user_id: int) -> str:
    """Return the current state for the user."""
    stack = _user_states.get(user_id, ["main"])
    return stack[-1]


class AdminTariffStates(StatesGroup):
    """States for the admin tariff configuration flow."""

    waiting_for_tariff_duration = State()
    waiting_for_tariff_price = State()
    waiting_for_tariff_name = State()
    editing_tariff_duration = State()
    editing_tariff_price = State()
    editing_tariff_name = State()


class AdminUserStates(StatesGroup):
    """States for admin user management actions."""

    assigning_points_amount = State()
    search_user_query = State()


class AdminContentStates(StatesGroup):
    """States related to posting content to channels."""

    waiting_for_channel_post_text = State()
    confirming_channel_post = State()


class AdminConfigStates(StatesGroup):
    """States for bot configuration options."""

    waiting_for_reaction_buttons = State()
    waiting_for_reaction_points = State()
    waiting_for_channel_choice = State()
    waiting_for_channel_interval = State()
    waiting_for_vip_interval = State()
    waiting_for_vip_channel_id = State()
    waiting_for_free_channel_id = State()
    waiting_for_reactions_input = State()
    waiting_for_points_input = State()


class AdminVipMessageStates(StatesGroup):
    """States for configuring VIP channel messages."""

    waiting_for_reminder_message = State()
    waiting_for_farewell_message = State()
    waiting_for_welcome_message = State()  # Este es el que falta
    waiting_for_expired_message = State()  # Este también podría ser necesario


class AdminMissionStates(StatesGroup):
    """States for creating missions from the admin panel."""

    creating_mission_name = State()
    creating_mission_description = State()
    creating_mission_type = State()
    creating_mission_target = State()
    creating_mission_reward = State()
    creating_mission_duration = State()


class AdminVipMissionStates(StatesGroup):
    """Simplified mission creation flow from the VIP config menu."""

    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_type = State()
    waiting_for_reward = State()
    waiting_for_activation = State()


class AdminBadgeStates(StatesGroup):
    creating_badge_name = State()
    creating_badge_description = State()
    creating_badge_requirement = State()
    creating_badge_emoji = State()
    deleting_badge = State()


class AdminDailyGiftStates(StatesGroup):
    """States for configuring the daily gift."""

    waiting_for_amount = State()


class AdminEventStates(StatesGroup):
    creating_event_name = State()
    creating_event_description = State()
    creating_event_multiplier = State()


class AdminRaffleStates(StatesGroup):
    creating_raffle_name = State()
    creating_raffle_description = State()
    creating_raffle_prize = State()


class AdminRewardStates(StatesGroup):
    """States for creating rewards from the admin panel."""

    creating_reward_name = State()
    creating_reward_points = State()
    creating_reward_description = State()
    creating_reward_type = State()

    editing_select_reward = State()
    editing_reward_name = State()
    editing_reward_points = State()
    editing_reward_description = State()
    editing_reward_type = State()


class AdminLevelStates(StatesGroup):
    """States for managing gamification levels."""

    creating_level_number = State()
    creating_level_name = State()
    creating_level_points = State()
    creating_level_reward = State()
    confirming_create_level = State()

    editing_level_number = State()
    editing_level_name = State()
    editing_level_points = State()
    editing_level_reward = State()

    deleting_level = State()


class AdminManualBadgeStates(StatesGroup):
    """States for manually awarding badges."""

    waiting_for_user = State()
    waiting_for_badge = State()


class AdminAuctionStates(StatesGroup):
    """States for managing auctions."""
    
    creating_auction_name = State()
    creating_auction_description = State()
    creating_auction_prize = State()
    creating_auction_initial_price = State()
    creating_auction_duration = State()
    creating_auction_settings = State()
    confirming_auction_creation = State()
    
    # Auction management states
    selecting_auction_to_end = State()
    selecting_auction_to_cancel = State()
    confirming_auction_action = State()


class AdminVipSubscriberStates(StatesGroup):
    """States for manual VIP subscription management."""

    waiting_for_days = State()
    waiting_for_new_date = State()
