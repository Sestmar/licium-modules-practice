from sqlalchemy import Boolean, String
from app.core.base import Base
from app.core.fields import field

class AssetLocation(Base):
    __tablename__ = "asset_lending_location"
    __abstract__ = False
    __model__ = "location"
    __service__ = "modules.asset_lending.services.lending.AssetLocationService"

    __selector_config__ = {
        "label_field": "name",
        "search_fields": ["name", "code"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "name", "label": "Nombre"},
            {"field": "code", "label": "Código"},
        ],
    }

    name = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Ubicación", "en": "Location"}},
    )
    code = field(
        String(50),
        required=True,
        public=True,
        editable=True,
        unique=True,
        info={"label": {"es": "Código", "en": "Code"}},
    )
    is_active = field(
        Boolean,
        required=True,
        public=True,
        editable=True,
        default=True,
        info={"label": {"es": "Activo", "en": "Active"}},
    )