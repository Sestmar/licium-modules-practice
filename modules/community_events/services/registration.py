import datetime as dt
from fastapi import HTTPException
from app.core.base import BaseService
from app.core.services import exposed_action
from app.core.serializer import serialize
from sqlalchemy import select

class RegistrationService(BaseService):
    from ..models.registration import Registration
    from ..models.event import Event

    def create(self, data: dict) -> dict:
        """Sobrescribe la creación base para calcular automáticamente si hay aforo."""
        event_id = data.get("event_id")
        event = self.repo.session.get(self.Event, int(event_id))
        
        # Traemos el evento de la base de datos
        # ESTO NOS DIRÁ LA VERDAD EN LOS LOGS 👇
        print(f"DEBUG: Evento ID {event_id} tiene estado: '{event.status if event else 'NO ENCONTRADO'}'")
        
        if not event or event.status != "published":
            raise HTTPException(status_code=400, detail=f"Error: El evento {event_id} tiene estado '{event.status if event else 'N/A'}'")
        
        if event.status != "published":
            raise HTTPException(status_code=400, detail="No se admiten inscripciones. El evento no está publicado.")

        # 2. Contamos cuántos confirmados hay en este evento usando SQLAlchemy
        stmt = select(self.Registration).where(
            self.Registration.event_id == int(event_id),
            self.Registration.status == "confirmed"
        )
        confirmed_count = len(self.repo.session.scalars(stmt).all())

        # 3. Lógica de aforo
        if confirmed_count >= (event.capacity_total or 0):
            data["status"] = "waitlist"
        else:
            data["status"] = "confirmed"

        # Dejamos que Licium cree el registro con el estado que hemos calculado
        return super().create(data)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def confirm(self, id: int, note: str | None = None) -> dict:
        reg = self.repo.session.get(self.Registration, int(id))
        if not reg: raise HTTPException(400, "Inscripción no encontrada")
        
        if reg.status == "cancelled":
            raise ValueError("No se puede confirmar una inscripción cancelada.")
        
        reg.status = "confirmed"
        self.repo.session.add(reg)
        self.repo.session.commit()
        self.repo.session.refresh(reg)
        return serialize(reg)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def move_waitlist(self, id: int, note: str | None = None) -> dict:
        reg = self.repo.session.get(self.Registration, int(id))
        if not reg: raise HTTPException(400, "Inscripción no encontrada")
        
        reg.status = "waitlist"
        self.repo.session.add(reg)
        self.repo.session.commit()
        self.repo.session.refresh(reg)
        return serialize(reg)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def checkin(self, id: int) -> dict:
        reg = self.repo.session.get(self.Registration, int(id))
        if not reg: raise HTTPException(400, "Inscripción no encontrada")
        
        if reg.status != "confirmed":
            raise ValueError("Solo los asistentes confirmados pueden hacer check-in.")
        if reg.checkin_at:
            raise ValueError("Este asistente ya ha entrado al evento.")
        
        reg.checkin_at = dt.datetime.now(dt.timezone.utc)
        self.repo.session.add(reg)
        self.repo.session.commit()
        self.repo.session.refresh(reg)
        return serialize(reg)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def bulk_checkin(self, ids: list[int]) -> dict:
        """Acción masiva para la vista de lista: Check-in a varios a la vez."""
        count = 0
        for reg_id in ids:
            reg = self.repo.session.get(self.Registration, int(reg_id))
            if reg and reg.status == "confirmed" and not reg.checkin_at:
                reg.checkin_at = dt.datetime.now(dt.timezone.utc)
                self.repo.session.add(reg)
                count += 1
                
        self.repo.session.commit()
        return {"message": {"es": f"Check-in completado para {count} asistentes.", "en": f"Check-in done for {count} attendees."}}