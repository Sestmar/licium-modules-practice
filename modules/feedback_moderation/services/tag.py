from app.core.base import BaseService

class TagService(BaseService):
    from ..models.tag import Tag
    # No se requieren acciones personalizadas, el CRUD base es suficiente.