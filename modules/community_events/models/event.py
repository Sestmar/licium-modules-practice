from __future__ import annotations
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

class Event(Base):
    __tablename__ = "community_event"
    __abstract__ = False
    __model__ = "community_events.event"
    __service__ = "modules.community_events.services.event.EventService"

    title = field(
        String(150),
        required=True,
        public=True,
        info={"label": {"es": "Título del Evento", "en": "Event Title"}}
    )
    slug = field(
        String(150),
        required=True,
        unique=True,
        public=True,
        info={"label": {"es": "Slug (URL)", "en": "Slug"}}
    )
    summary = field(
        String(255),
        required=False,
        public=True,
        info={"label": {"es": "Resumen", "en": "Summary"}}
    )
    description = field(
        Text,
        required=False,
        public=True,
        info={"label": {"es": "Descripción", "en": "Description"}}
    )
    status = field(
        String(50),
        default="draft",
        public=True,
        info={
            "label": {"es": "Estado", "en": "Status"},
            "choices": [
                {"value": "draft", "label": {"es": "Borrador", "en": "Draft"}},
                {"value": "published", "label": {"es": "Publicado", "en": "Published"}},
                {"value": "closed", "label": {"es": "Cerrado", "en": "Closed"}},
                {"value": "cancelled", "label": {"es": "Cancelado", "en": "Cancelled"}}
            ]
        }
    )
    start_at = field(
        DateTime(timezone=True),
        required=True,
        public=True,
        info={"label": {"es": "Fecha de inicio", "en": "Start Date"}}
    )
    end_at = field(
        DateTime(timezone=True),
        required=True,
        public=True,
        info={"label": {"es": "Fecha de fin", "en": "End Date"}}
    )
    location = field(
        String(255),
        required=False,
        public=True,
        info={"label": {"es": "Ubicación", "en": "Location"}}
    )
    capacity_total = field(
        Integer,
        required=True,
        default=0,
        public=True,
        info={"label": {"es": "Aforo Total", "en": "Total Capacity"}}
    )
    is_public = field(
        Boolean,
        default=False,
        public=True,
        info={"label": {"es": "Es Público", "en": "Is Public"}}
    )
    
    # ¡Nuestra famosa FK a core_user con Uuid!
    organizer_user_id = field(
        Uuid,
        ForeignKey("core_user.id", ondelete="SET NULL"),
        required=False,
        public=True,
        info={"label": {"es": "Organizador", "en": "Organizer"}}
    )

    # Relaciones que conectaremos enseguida
    sessions = relationship("EventSession", back_populates="event", cascade="all, delete-orphan")
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")