from sqlalchemy import String, Text, ForeignKey, Uuid, Integer
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

class Asset(Base):
    __tablename__ = "asset_lending_asset"
    __abstract__ = False
    __model__ = "asset"
    __service__ = "modules.asset_lending.services.lending.AssetService"

    __selector_config__ = {
        "label_field": "name",
        "search_fields": ["name", "asset_code", "status"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "name", "label": "Recurso"},
            {"field": "asset_code", "label": "Código"},
        ],
    }

    name = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Nombre", "en": "Name"}},
    )
    asset_code = field(
        String(50),
        required=True,
        public=True,
        editable=True,
        unique=True,
        info={"label": {"es": "Código de Activo", "en": "Asset Code"}},
    )
    status = field(
        String(20),
        required=True,
        public=True,
        editable=True,
        default="available",
        info={"label": {"es": "Estado", "en": "Status"}},
    )
    notes = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Notas", "en": "Notes"}},
    )
    location_id = field(
        Integer,
        ForeignKey("asset_lending_location.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Ubicación", "en": "Location"}},
    )
    location = relationship(
        "modules.asset_lending.models.location.AssetLocation",
        foreign_keys=lambda: [Asset.location_id],
        info={"public": True, "recursive": False, "editable": True},
    )
    responsible_user_id = field(
        Uuid,
        ForeignKey("core_user.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Responsable", "en": "Responsible User"}},
    )