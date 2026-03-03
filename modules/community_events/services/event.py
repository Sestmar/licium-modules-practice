from app.core.base import BaseService, exposed_action
from app.core.exceptions import UserError

class EventService(BaseService):
    __model__ = "community_events.event"

    @exposed_action({
        "label": {"es": "Publicar Evento", "en": "Publish Event"}, 
        "icon": "mdi-earth"
    })
    def publish_event(self, id: str, note: str | None = None) -> None:
        """Cambia el evento de borrador a publicado."""
        event = self.read(id)
        if event.status != "draft":
            raise UserError("Solo se pueden publicar eventos que estén en estado borrador.")
        
        self.update(id, {"status": "published"})
        # Si tuviéramos un sistema de logs, aquí guardaríamos la 'note'

    @exposed_action({
        "label": {"es": "Cerrar Inscripciones", "en": "Close Registration"}, 
        "icon": "mdi-door-closed",
        "color": "warning"
    })
    def close_registration(self, id: str, reason: str | None = None) -> None:
        """Cierra el evento para que no entren más inscripciones."""
        event = self.read(id)
        if event.status != "published":
            raise UserError("Solo se pueden cerrar eventos que actualmente estén publicados.")
        
        self.update(id, {"status": "closed"})

    @exposed_action({
        "label": {"es": "Cancelar Evento", "en": "Cancel Event"}, 
        "icon": "mdi-cancel", 
        "color": "error"
    })
    # Fíjate que 'reason' NO tiene '= None'. Licium hará que este campo sea obligatorio en el modal.
    def cancel_event(self, id: str, reason: str) -> None:
        """Cancela el evento por fuerza mayor."""
        event = self.read(id)
        if event.status == "cancelled":
            raise UserError("El evento ya está cancelado.")
        
        self.update(id, {"status": "cancelled"})

    @exposed_action({
        "label": {"es": "Reabrir Evento", "en": "Reopen Event"}, 
        "icon": "mdi-refresh"
    })
    def reopen_event(self, id: str) -> None:
        """Vuelve a abrir un evento cerrado o cancelado."""
        event = self.read(id)
        if event.status not in ["closed", "cancelled"]:
            raise UserError("Solo se pueden reabrir eventos que estén cerrados o cancelados.")
        
        self.update(id, {"status": "published"})