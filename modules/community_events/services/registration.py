from app.core.base import BaseService, exposed_action
from datetime import datetime, timezone

class RegistrationService(BaseService):
    __model__ = "community_events.registration"

    @exposed_action({
        "label": {"es": "Inscribir", "en": "Register"}, 
        "icon": "mdi-account-plus"
    })
    def register(self, event_id: str, attendee_name: str, attendee_email: str, session_id: str | None = None) -> str:
        """Crea una inscripción calculando automáticamente si hay aforo."""
        # 1. Obtenemos el evento usando el entorno de Licium (self.env)
        event_service = self.env.get_service("modules.community_events.services.event.EventService")
        event = event_service.read(event_id)
        
        if event.status != "published":
            raise ValueError("No se admiten inscripciones. El evento no está publicado.")
            
        # 2. Contamos cuántos confirmados hay ya en este evento
        domain = [("event_id", "=", event_id), ("status", "=", "confirmed")]
        confirmed_count = self.search_count(domain)
        
        # 3. Lógica de aforo (¡Aquí está la magia!)
        status = "confirmed"
        if confirmed_count >= event.capacity_total:
            status = "waitlist" # Si está lleno, a la lista de espera
            
        # 4. Creamos el registro
        data = {
            "event_id": event_id,
            "attendee_name": attendee_name,
            "attendee_email": attendee_email,
            "session_id": session_id,
            "status": status
        }
        return self.create(data)

    @exposed_action({
        "label": {"es": "Confirmar Manual", "en": "Confirm"}, 
        "icon": "mdi-check-circle", 
        "color": "success"
    })
    def confirm(self, id: str, note: str | None = None) -> None:
        reg = self.read(id)
        if reg.status == "cancelled":
            raise ValueError("No se puede confirmar una inscripción cancelada.")
        self.update(id, {"status": "confirmed", "notes": note})

    @exposed_action({
        "label": {"es": "A Lista Espera", "en": "Move Waitlist"}, 
        "icon": "mdi-clock-outline",
        "color": "warning"
    })
    def move_waitlist(self, id: str, note: str | None = None) -> None:
        self.update(id, {"status": "waitlist", "notes": note})

    @exposed_action({
        "label": {"es": "Check-in Individual", "en": "Check-in"}, 
        "icon": "mdi-map-marker-check", 
        "color": "info"
    })
    def checkin(self, id: str, source: str = "manual") -> None:
        reg = self.read(id)
        if reg.status != "confirmed":
            raise ValueError("Solo los asistentes confirmados pueden hacer check-in.")
        if reg.checkin_at:
            raise ValueError("Este asistente ya ha entrado al evento.")
        
        self.update(id, {"checkin_at": datetime.now(timezone.utc)})

    # Importante --> bulk=True permite seleccionar varios en la tabla de golpe
    @exposed_action({
        "label": {"es": "Check-in Masivo", "en": "Bulk Check-in"}, 
        "icon": "mdi-account-group", 
        "bulk": True,
        "color": "primary"
    })
    def bulk_checkin(self, ids: list[str]) -> dict:
        """Acción para la vista de lista: Check-in a varios a la vez."""
        count = 0
        for reg_id in ids:
            reg = self.read(reg_id)
            if reg.status == "confirmed" and not reg.checkin_at:
                self.update(reg_id, {"checkin_at": datetime.now(timezone.utc)})
                count += 1
                
        return {"message": {"es": f"Check-in completado para {count} asistentes.", "en": f"Check-in done for {count} attendees."}}