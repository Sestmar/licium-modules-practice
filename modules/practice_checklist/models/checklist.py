from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import backref, relationship
from app.core.base import Base
from app.core.fields import field


class PracticeChecklist(Base):
    __tablename__ = "practice_checklist"
    __abstract__ = False
    __model__ = "checklist"
    __service__ = "modules.practice_checklist.services.checklist.PracticeChecklistService"

    __selector_config__ = {
        "label_field": "name",
        "search_fields": ["name", "status", "description"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "name", "label": "Checklist"},
            {"field": "status", "label": "Estado"},
            {"field": "is_public", "label": "Público"},
        ],
    }

    name = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Checklist", "en": "Checklist"}},
    )
    description = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Descripción", "en": "Description"}},
    )
    status = field(
        String(20),
        required=True,
        public=True,
        editable=True,
        default="draft",
        info={
            "label": {"es": "Estado", "en": "Status"},
            "choices": [
                {"label": "Draft", "value": "draft"},
                {"label": "Open", "value": "open"},
                {"label": "Closed", "value": "closed"},
            ],
        },
    )
    is_public = field(
        Boolean,
        required=True,
        public=True,
        editable=True,
        default=False,
        info={"label": {"es": "Público", "en": "Public"}},
    )
    owner_id = field(
        Uuid,
        ForeignKey("core_user.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Responsable", "en": "Owner"}},
    )
    owner = relationship(
        "User",
        foreign_keys=lambda: [PracticeChecklist.owner_id],
        info={"public": True, "recursive": False, "editable": True},
    )
    closed_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Cerrado en", "en": "Closed at"}},
    )


class PracticeChecklistItem(Base):
    __tablename__ = "practice_checklist_item"
    __abstract__ = False
    __model__ = "checklist_item"
    __service__ = "modules.practice_checklist.services.checklist.PracticeChecklistItemService"

    __selector_config__ = {
        "label_field": "title",
        "search_fields": ["title", "note"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "checklist", "label": "Checklist"},
            {"field": "title", "label": "Ítem"},
            {"field": "is_done", "label": "Hecho"},
        ],
    }

    checklist_id = field(
        Integer,
        ForeignKey("practice_checklist.id", ondelete="CASCADE"),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Checklist", "en": "Checklist"}},
    )
    checklist = relationship(
        "modules.practice_checklist.models.checklist.PracticeChecklist",
        foreign_keys=lambda: [PracticeChecklistItem.checklist_id],
        backref=backref("items", cascade="all, delete-orphan"),
        info={"public": True, "recursive": False, "editable": True},
    )
    title = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Ítem", "en": "Item"}},
    )
    note = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Nota", "en": "Note"}},
    )
    assigned_user_id = field(
        Uuid,
        ForeignKey("core_user.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Asignado a", "en": "Assigned to"}},
    )
    assigned_user = relationship(
        "User",
        foreign_keys=lambda: [PracticeChecklistItem.assigned_user_id],
        info={"public": True, "recursive": False, "editable": True},
    )
    is_done = field(
        Boolean,
        required=True,
        public=True,
        editable=True,
        default=False,
        info={"label": {"es": "Hecho", "en": "Done"}},
    )
    done_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Hecho en", "en": "Done at"}},
    )