from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

# Tabla de asociación M2M para Suggestion <-> Tag
suggestion_tag_rel = Table(
    "feedback_moderation_suggestion_tag_rel",
    Base.metadata,
    Column("suggestion_id", Integer, ForeignKey("feedback_moderation_suggestion.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("feedback_moderation_tag.id", ondelete="CASCADE"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "feedback_moderation_tag"
    __abstract__ = False
    __model__ = "tag"
    __service__ = "modules.feedback_moderation.services.tag.TagService"

    __selector_config__ = {
        "label_field": "name",
        "search_fields": ["name", "slug"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "name", "label": "Nombre"},
            {"field": "slug", "label": "Slug"},
            {"field": "color", "label": "Color"},
        ],
    }

    name = field(
        String(100),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Nombre", "en": "Name"}},
    )
    slug = field(
        String(100),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Slug", "en": "Slug"}},
    )
    color = field(
        String(20),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Color (Hex)", "en": "Color (Hex)"}},
    )

    # Relación inversa M2M (opcional, pero buena práctica)
    suggestions = relationship(
        "Suggestion",
        secondary=suggestion_tag_rel,
        back_populates="tags",
        info={"public": True, "recursive": False, "editable": True},
    )