import re
from .config import ADMIN_IDS


def sanitize_text(value: str | None) -> str | None:
    """Remove characters that cannot be encoded in UTF-8."""
    if value is None:
        return None
    return value.encode("utf-8", "ignore").decode("utf-8", "ignore")


def anonymize_username(user, current_user_id: int, admin_ids: list[int] | None = None) -> str:
    """
    Anonymize username for display, showing full info only to the viewer and admins.
    
    Args:
        user: User object with id, username, first_name, last_name
        current_user_id: ID of the user viewing the information
        admin_ids: Optional list of admin IDs to show without anonymization
        
    Returns:
        str: Full name/username for own user, anonymized for others
    """
    if not user:
        return "Usuario desconocido"

    if admin_ids is None:
        admin_ids = ADMIN_IDS
    
    # Show full info to the user themselves or if user is admin
    if user.id == current_user_id or user.id in admin_ids:
        if user.username:
            return f"@{user.username}"
        elif user.first_name:
            full_name = user.first_name
            if user.last_name:
                full_name += f" {user.last_name}"
            return full_name
        else:
            return f"Usuario {user.id}"
    
    # Anonymize for other users
    if user.username:
        return _anonymize_string(user.username)
    elif user.first_name:
        first_anon = _anonymize_string(user.first_name)
        if user.last_name:
            last_anon = _anonymize_string(user.last_name)
            return f"{first_anon} {last_anon}"
        return first_anon
    else:
        # Fallback to anonymized user ID
        user_id_str = str(user.id)
        if len(user_id_str) > 3:
            return f"U{user_id_str[:2]}***{user_id_str[-1]}"
        else:
            return f"U***{user_id_str[-1]}"


def _anonymize_string(text: str) -> str:
    """
    Anonymize a string by showing first character and asterisks.
    
    Args:
        text: String to anonymize
        
    Returns:
        str: Anonymized string (e.g., "John" -> "J***")
    """
    if not text or len(text) == 0:
        return "***"
    elif len(text) == 1:
        return "*"
    elif len(text) == 2:
        return f"{text[0]}*"
    elif len(text) <= 4:
        return f"{text[0]}**{text[-1]}"
    else:
        return f"{text[0]}***{text[-1]}"


def format_points(points: float) -> str:
    """Format points for display, removing unnecessary decimals."""
    if points == int(points):
        return str(int(points))
    else:
        return f"{points:.1f}"


def format_time_remaining(end_time) -> str:
    """Format remaining time for auctions."""
    from datetime import datetime
    
    if not end_time:
        return "Sin límite"
    
    now = datetime.utcnow()
    if end_time <= now:
        return "Finalizada"
    
    diff = end_time - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
