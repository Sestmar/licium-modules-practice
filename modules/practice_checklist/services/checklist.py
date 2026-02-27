from __future__ import annotations
import datetime as dt
from fastapi import HTTPException
from app.core.base import BaseService
from app.core.context import get_current_user_id
from app.core.serializer import serialize
from app.core.services import exposed_action

from ..models import PracticeChecklist, PracticeChecklistItem


class PracticeChecklistService(BaseService):
    from ..models import PracticeChecklist

    def create(self, obj):  # type: ignore[override]
        if not isinstance(obj, dict):
            return super().create(obj)
        payload = dict(obj)
        if not payload.get("owner_id"):
            payload["owner_id"] = get_current_user_id()
        if not payload.get("status"):
            payload["status"] = "open"
        return super().create(payload)

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def close(self, id: int, close_note: str | None = None, make_public: bool = False) -> dict:
        rec = self.repo.session.get(PracticeChecklist, int(id))
        if rec is None:
            raise HTTPException(404, "Checklist not found")
        rec.status = "closed"
        rec.is_public = bool(make_public)
        rec.closed_at = dt.datetime.now(dt.timezone.utc)
        if close_note:
            base = (rec.description or "").strip()
            rec.description = f"{base}\n\n[Cierre] {close_note}".strip()
        self.repo.session.add(rec)
        self.repo.session.commit()
        self.repo.session.refresh(rec)
        return serialize(rec)

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def reopen(self, id: int) -> dict:
        rec = self.repo.session.get(PracticeChecklist, int(id))
        if rec is None:
            raise HTTPException(404, "Checklist not found")
        rec.status = "open"
        rec.closed_at = None
        self.repo.session.add(rec)
        self.repo.session.commit()
        self.repo.session.refresh(rec)
        return serialize(rec)


class PracticeChecklistItemService(BaseService):
    from ..models import PracticeChecklistItem

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def set_done(self, id: int, done: bool = True, note: str | None = None) -> dict:
        item = self.repo.session.get(PracticeChecklistItem, int(id))
        if item is None:
            raise HTTPException(404, "Checklist item not found")
        item.is_done = bool(done)
        item.done_at = dt.datetime.now(dt.timezone.utc) if done else None
        if note:
            base = (item.note or "").strip()
            item.note = f"{base}\n\n[Estado] {note}".strip()
        self.repo.session.add(item)
        self.repo.session.commit()
        self.repo.session.refresh(item)
        return serialize(item)
    
    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def bulk_set_done(self, id: list[int], done: bool = True) -> dict:
        # Importación local para evitar errores de carga circular
        from ..models.checklist import PracticeChecklistItem
        
        items = self.repo.session.query(PracticeChecklistItem).filter(PracticeChecklistItem.id.in_(id)).all()
        
        now = dt.datetime.now(dt.timezone.utc)
        for item in items:
            item.is_done = bool(done)
            item.done_at = now if done else None
            self.repo.session.add(item)
            
        self.repo.session.commit()
        return {"message": f"{len(items)} ítems actualizados"}