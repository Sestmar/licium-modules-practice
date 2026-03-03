from __future__ import annotations
from sqlalchemy import String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.base import Base
from app.core.fields import field

class Registration(Base):
    __tablename__ = "community_event_registration"
    __abstract__ = False
    __model__ = "community_events.registration"
    __service__ = "modules.community_events.services.registration.RegistrationService"

    event_id = field(
        Uuid,
        ForeignKey("community_event.id", ondelete="CASCADE"),
        required=True,
        public=True,
        info={"label": {"es": "Evento", "en": "Event"}}
    )
    session_id = field(
        Uuid,
        ForeignKey("community_event_session.id", ondelete="SET NULL"),
        required=False,
        public=True,
        info={"label": {"es": "Sesión (Opcional)", "en": "Session"}}
    )
    attendee_name = field(
        String(150),
        required=True,
        public=True,
        info={"label": {"es": "Nombre Asistente", "en": "Attendee Name"}}
    )
    attendee_email = field(
        String(150),
        required=True,
        public=True,
        info={"label": {"es": "Email", "en": "Email"}}
    )
    # ¡Otra vez el UUID para el usuario registrado!
    attendee_user_id = field(
        Uuid,
        ForeignKey("core_user.id", ondelete="SET NULL"),
        required=False,
        public=True,
        info={"label": {"es": "Usuario (Si está logueado)", "en": "User"}}
    )
    status = field(
        String(50),
        default="pending",
        public=True,
        info={
            "label": {"es": "Estado", "en": "Status"},
            "choices": [
                {"value": "pending", "label": {"es": "Pendiente", "en": "Pending"}},
                {"value": "confirmed", "label": {"es": "Confirmada", "en": "Confirmed"}},
                {"value": "waitlist", "label": {"es": "Lista de Espera", "en": "Waitlist"}},
                {"value": "cancelled", "label": {"es": "Cancelada", "en": "Cancelled"}}
            ]
        }
    )
    registered_at = field(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        public=True,
        info={"label": {"es": "Fecha de Registro", "en": "Registered At"}}
    )
    checkin_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        info={"label": {"es": "Fecha de Check-in", "en": "Check-in Date"}}
    )
    notes = field(
        Text,
        required=False,
        public=True,
        info={"label": {"es": "Notas", "en": "Notes"}}
    )

    # Relaciones
    event = relationship("Event", back_populates="registrations")
    session = relationship("EventSession", back_populates="registrations")