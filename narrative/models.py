from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserNarrativeState(Base):
    __tablename__ = "user_narrative_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    current_story_node = Column(String, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relación con decisiones del usuario
    decisions = relationship(
        "UserDecision",
        back_populates="narrative_state",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    user = relationship("User", back_populates="narrative_state", lazy="selectin")


class UserDecision(Base):
    __tablename__ = "user_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_narrative_state_id = Column(Integer, ForeignKey("user_narrative_states.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision_code = Column(String, nullable=False)
    decision_text = Column(Text, nullable=True)
    made_at = Column(DateTime, default=func.now())

    narrative_state = relationship("UserNarrativeState", back_populates="decisions")
    # Opcional: relación con User si se requiere
    # user = relationship("User")
