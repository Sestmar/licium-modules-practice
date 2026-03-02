from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

# Importo la tabla intermedia y el modelo Tag
from .tag import suggestion_tag_rel, Tag

class Suggestion(Base):
    __tablename__ = "feedback_moderation_suggestion"
    __abstract__ = False
    __model__ = "suggestion"
    __service__ = "modules.feedback_moderation.services.suggestion.SuggestionService"

    __selector_config__ = {
        "label_field": "title",
        "search_fields": ["title", "author_email", "status"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "title", "label": "Título"},
            {"field": "status", "label": "Estado"},
            {"field": "author_email", "label": "Email Autor"},
            {"field": "is_public", "label": "Público"},
        ],
    }

    title = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Título", "en": "Title"}},
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
                {"label": "Fusionado", "value": "merged"},
            ],
        },
    )
    author_name = field(
        String(100),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Nombre del autor", "en": "Author Name"}},
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
    moderation_note = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Nota de moderación", "en": "Moderation Note"}},
    )
    published_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Publicado en", "en": "Published at"}},
    )
    reviewed_by_id = field(
        Uuid,
        ForeignKey("core_user.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Revisado por", "en": "Reviewed by"}},
    )
    
    # --- Relaciones ---
    
    reviewed_by = relationship(
        "User",
        foreign_keys=lambda: [Suggestion.reviewed_by_id],
        info={"public": True, "recursive": False, "editable": True},
    )
    
    # Relación Many-to-Many con Tag, definiendo el dict 'info' correctamente
    tags = relationship(
        "Tag", 
        secondary=suggestion_tag_rel, 
        back_populates="suggestions", 
        info={
            "public": True, 
            "recursive": False, 
            "editable": True, 
            "label": {"es": "Etiquetas", "en": "Tags"}
        }
    )