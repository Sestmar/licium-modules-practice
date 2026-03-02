from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field


class Comment(Base):
    __tablename__ = "feedback_moderation_comment"
    __abstract__ = False
    __model__ = "comment"
    __service__ = "modules.feedback_moderation.services.comment.CommentService"

    __selector_config__ = {
        "label_field": "id",
        "search_fields": ["content", "author_email", "status"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "suggestion_id", "label": "Sugerencia ID"},
            {"field": "status", "label": "Estado"},
            {"field": "author_email", "label": "Email Autor"},
            {"field": "is_public", "label": "Público"},
        ],
    }

    suggestion_id = field(
        Integer,
        ForeignKey("feedback_moderation_suggestion.id", ondelete="CASCADE"),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Sugerencia", "en": "Suggestion"}},
    )
    content = field(
        Text,
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Contenido", "en": "Content"}},
    )
    status = field(
        String(20),
        required=True,
        public=True,
        editable=True,
        default="pending",
        info={
            "label": {"es": "Estado", "en": "Status"},
            "choices": [
                {"label": "Pendiente", "value": "pending"},
                {"label": "Publicado", "value": "published"},
                {"label": "Rechazado", "value": "rejected"},
            ],
        },
    )
    author_email = field(
        String(150),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Email del autor", "en": "Author Email"}},
    )
    is_public = field(
        Boolean,
        required=True,
        public=True,
        editable=True,
        default=False,
        info={"label": {"es": "Público", "en": "Public"}},
    )
    published_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Publicado en", "en": "Published at"}},
    )

    # Relación ORM
    suggestion = relationship(
        "Suggestion",
        foreign_keys=lambda: [Comment.suggestion_id],
        info={"public": True, "recursive": False, "editable": True},
    )