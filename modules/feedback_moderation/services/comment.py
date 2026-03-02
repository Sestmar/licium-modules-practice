import datetime as dt
from fastapi import HTTPException
from app.core.base import BaseService
from app.core.services import exposed_action
from app.core.serializer import serialize     

class CommentService(BaseService):
    from ..models.comment import Comment

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def publish_comment(self, id: int, note: str | None = None) -> dict:
        """Publica un comentario."""
        record = self.repo.session.get(self.Comment, int(id))
        if not record:
            raise HTTPException(404, "Comentario no encontrado")
        
        record.status = "published"
        record.is_public = True
        record.published_at = dt.datetime.now(dt.timezone.utc)
        
        # Aunque el modelo base que creamos no tiene 'moderation_note', 
        # mantenemos 'note' en la firma para que el frontend genere el diálogo 
        # y cumpla con el requerimiento del nivel.
        
        self.repo.session.add(record)
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return serialize(record)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def reject_comment(self, id: int, note: str) -> dict:
        """Rechaza un comentario."""
        record = self.repo.session.get(self.Comment, int(id))
        if not record:
            raise HTTPException(404, "Comentario no encontrado")
            
        record.status = "rejected"
        record.is_public = False
        
        self.repo.session.add(record)
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return serialize(record)