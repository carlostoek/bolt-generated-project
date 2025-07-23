from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HintCombination(AsyncAttrs, Base):
    __tablename__ = "hint_combinations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    combination_code = Column(String, unique=True, nullable=False)  # Código que representa la combinación correcta
    required_hints = Column(String, nullable=False)  # IDs o códigos separados por coma, ejemplo: "2,4,7"
    reward_code = Column(String, nullable=False)  # Código de la pista o recompensa que se desbloquea
    created_at = Column(DateTime, default=func.now())
