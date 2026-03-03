from fastapi import HTTPException
from app.core.base import BaseService
from app.core.services import exposed_action
from app.core.serializer import serialize

class EventService(BaseService):
    from ..models.event import Event

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def publish_event(self, id: int, note: str | None = None) -> dict:
        """Cambia el evento de borrador a publicado."""
        event = self.repo.session.get(self.Event, int(id))
        if not event:
            raise HTTPException(400, "Evento no encontrado")
        
        if event.status != "draft":
            raise ValueError("Solo se pueden publicar eventos que estén en estado borrador.")
        
        event.status = "published"
        self.repo.session.add(event)
        self.repo.session.commit()
        self.repo.session.refresh(event)
        return serialize(event)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def close_registration(self, id: int, reason: str | None = None) -> dict:
        """Cierra el evento para que no entren más inscripciones."""
        event = self.repo.session.get(self.Event, int(id))
        if not event:
            raise HTTPException(400, "Evento no encontrado")
        
        if event.status != "published":
            raise ValueError("Solo se pueden cerrar eventos que actualmente estén publicados.")
        
        event.status = "closed"
        self.repo.session.add(event)
        self.repo.session.commit()
        self.repo.session.refresh(event)
        return serialize(event)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def cancel_event(self, id: int, reason: str | None = None) -> dict:
        """Cancela el evento por fuerza mayor."""
        event = self.repo.session.get(self.Event, int(id))
        if not event:
            raise HTTPException(400, "Evento no encontrado")
        
        if event.status == "cancelled":
            raise ValueError("El evento ya está cancelado.")
        
        event.status = "cancelled"
        self.repo.session.add(event)
        self.repo.session.commit()
        self.repo.session.refresh(event)
        return serialize(event)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def reopen_event(self, id: int) -> dict:
        """Vuelve a abrir un evento cerrado o cancelado."""
        event = self.repo.session.get(self.Event, int(id))
        if not event:
            raise HTTPException(404, "Evento no encontrado")
        
        if event.status not in ["closed", "cancelled"]:
            raise ValueError("Solo se pueden reabrir eventos que estén cerrados o cancelados.")
        
        event.status = "published"
        self.repo.session.add(event)
        self.repo.session.commit()
        self.repo.session.refresh(event)
        return serialize(event)