# database/models.py
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
from uuid import uuid4
from sqlalchemy.sql import func
from sqlalchemy.future import select
import enum
from .base import Base
from sqlalchemy import Column, BigInteger, String, Float, Integer, JSON, DateTime
from sqlalchemy.orm import relationship, declared_attr

# --- IMPORTS EXPLÍCITOS DE MODELOS DE NARRATIVA PARA REGISTRAR TABLAS ---
from narrative.models import (
    StoryFragment,
    UserNarrativeState,
    UserDecision,
    NarrativeMetrics,
)

# ... (resto del archivo sin cambios, modelos de gamificación, etc.)

class AuctionStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"

# ... (resto del archivo sin cambios, todos los modelos como antes)
# (NO MODIFICAR el resto del contenido, solo agregar los imports de arriba)
