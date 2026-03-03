from __future__ import annotations
from sqlalchemy import String, Integer, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

class EventSession(Base):
    __tablename__ = "community_event_session"
    __abstract__ = False
    __model__ = "community_events.session"
    __service__ = "modules.community_events.services.session.SessionService"

    event_id = field(
        Uuid,
        ForeignKey("community_event.id", ondelete="CASCADE"),
        required=True,
        public=True,
        info={"label": {"es": "Evento", "en": "Event"}}
    )
    title = field(
        String(150),
        required=True,
        public=True,
        info={"label": {"es": "Título de la Sesión", "en": "Session Title"}}
    )
    start_at = field(
        DateTime(timezone=True),
        required=True,
        public=True,
        info={"label": {"es": "Inicio", "en": "Start"}}
    )
    end_at = field(
        DateTime(timezone=True),
        required=True,
        public=True,
        info={"label": {"es": "Fin", "en": "End"}}
    )
    speaker_name = field(
        String(150),
        required=False,
        public=True,
        info={"label": {"es": "Ponente", "en": "Speaker"}}
    )
    room = field(
        String(100),
        required=False,
        public=True,
        info={"label": {"es": "Sala", "en": "Room"}}
    )
    capacity = field(
        Integer,
        required=False,
        public=True,
        info={"label": {"es": "Aforo Sesión", "en": "Session Capacity"}}
    )
    status = field(
        String(50),
        default="active",
        public=True,
        info={
            "label": {"es": "Estado", "en": "Status"},
            "choices": [
                {"value": "active", "label": {"es": "Activa", "en": "Active"}},
                {"value": "cancelled", "label": {"es": "Cancelada", "en": "Cancelled"}}
            ]
        }
    )

    # Relaciones
    event = relationship("Event", back_populates="sessions")
    # registrations = relationship("Registration", back_populates="session", cascade="all, delete-orphan")