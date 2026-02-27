from sqlalchemy import String, Text, ForeignKey, Uuid, DateTime, Integer
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

class AssetLoan(Base):
    __tablename__ = "asset_lending_loan"
    __abstract__ = False
    __model__ = "loan"
    __service__ = "modules.asset_lending.services.lending.AssetLoanService"

    __selector_config__ = {
        "label_field": "id",
        "search_fields": ["status"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "status", "label": "Estado"},
        ],
    }

    asset_id = field(
        Integer,
        ForeignKey("asset_lending_asset.id"),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Recurso", "en": "Asset"}},
    )
    borrower_user_id = field(
        Uuid,
        ForeignKey("core_user.id"),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Prestatario", "en": "Borrower"}},
    )
    checkout_at = field(
        DateTime(timezone=True),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Fecha de Salida", "en": "Checkout At"}},
    )
    due_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Fecha Límite", "en": "Due At"}},
    )
    returned_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Devuelto en", "en": "Returned At"}},
    )
    status = field(
        String(20),
        required=True,
        public=True,
        editable=True,
        default="open",
        info={"label": {"es": "Estado", "en": "Status"}},
    )
    checkout_note = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Nota de salida", "en": "Checkout Note"}},
    )
    return_note = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Nota de devolución", "en": "Return Note"}},
    )