import datetime as dt
from fastapi import HTTPException
from app.core.base import BaseService
from app.core.services import exposed_action
from app.core.serializer import serialize

class SuggestionService(BaseService):
    from ..models.suggestion import Suggestion

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def publish(self, id: int, note: str | None = None, pin: bool = False) -> dict:
        """Publica una sugerencia y la hace visible al público."""
        record = self.repo.session.get(self.Suggestion, int(id))
        if not record:
            raise HTTPException(404, "Sugerencia no encontrada")
        
        if record.status == "published":
            raise HTTPException(400, "Esta sugerencia ya está publicada.")

        # Cambiamos estado y visibilidad
        record.status = "published"
        record.is_public = True
        record.published_at = dt.datetime.now(dt.timezone.utc)
        
        if note:
            record.moderation_note = note

        # Nota: El parámetro 'pin' lo pide el enunciado. Si tuvieras un campo 'is_pinned' en el modelo, lo asignarías aquí.
        
        self.repo.session.add(record)
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return serialize(record)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def reject(self, id: int, note: str) -> dict:
        """Rechaza una sugerencia (el note es obligatorio para justificar)."""
        record = self.repo.session.get(self.Suggestion, int(id))
        if not record:
            raise HTTPException(404, "Sugerencia no encontrada")

        record.status = "rejected"
        record.is_public = False
        record.moderation_note = note  # Al no tener " | None", el frontend lo pedirá como campo obligatorio

        self.repo.session.add(record)
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return serialize(record)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def merge(self, id: int, target_id: int, note: str | None = None) -> dict:
        """Fusiona esta sugerencia indicando que es un duplicado de 'target_id'."""
        record = self.repo.session.get(self.Suggestion, int(id))
        target_record = self.repo.session.get(self.Suggestion, int(target_id))
        
        if not record or not target_record:
            raise HTTPException(404, "Una de las sugerencias no existe")
            
        if id == target_id:
            raise HTTPException(400, "No puedes fusionar una sugerencia consigo misma")

        record.status = "merged"
        record.is_public = False
        
        # Generamos una nota automática si el moderador no escribe una
        nota_merge = note if note else f"Fusionado con la sugerencia #{target_id}"
        record.moderation_note = nota_merge

        self.repo.session.add(record)
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return serialize(record)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def reopen(self, id: int) -> dict:
        """Devuelve una sugerencia a estado pendiente."""
        record = self.repo.session.get(self.Suggestion, int(id))
        if not record:
            raise HTTPException(404, "Sugerencia no encontrada")

        record.status = "pending"
        record.is_public = False
        record.published_at = None
        record.moderation_note = None

        self.repo.session.add(record)
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return serialize(record)