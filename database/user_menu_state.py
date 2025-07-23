# database/user_menu_state.py
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.base_models import User

async def set_user_menu_state(session: AsyncSession, user_id: int, menu_state: str):
  """
  Actualiza el estado de menú del usuario en la base de datos.
  """
  result = await session.execute(select(User).where(User.id == user_id))
  user = result.scalar_one_or_none()
  if user:
    user.menu_state = menu_state
    await session.commit()
