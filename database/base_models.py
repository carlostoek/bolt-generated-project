# database/base_models.py
from sqlalchemy import (
  Column,
  Integer,
  String,
  BigInteger,
  DateTime,
  Boolean,
  JSON,
  Text,
  ForeignKey,
  Float,
  UniqueConstraint,
  Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# --- MODELOS BASE ---

class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, autoincrement=True)
  username = Column(String, unique=True, nullable=False)
  # ... otros campos relevantes ...
  # Relación con narrativa
  narrative_state = relationship("UserNarrativeState", back_populates="user", uselist=False, lazy="selectin")

# Aquí puedes agregar otros modelos base compartidos si es necesario.
