import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

# Ajusta estas rutas si tu estructura difiere ligeramente
from ..models.suggestion import Suggestion
from ..services.suggestion import SuggestionService

@pytest.fixture
def mock_service():
    """Crea una instancia del servicio con una base de datos (repositorio) simulada."""
    # 1. Creamos la base de datos de mentira primero
    mock_repo = MagicMock()
    mock_repo.session = MagicMock()
    
    # 2. Se la pasamos al servicio al crearlo
    service = SuggestionService(mock_repo) 
    
    return service

def test_publish_suggestion_success(mock_service):
    # 1. Preparamos una sugerencia en estado "pending"
    mock_suggestion = Suggestion(id=1, status="pending", is_public=False)
    mock_service.repo.session.get.return_value = mock_suggestion

    # 2. Ejecutamos la acción de publicar
    mock_service.publish(id=1, note="Buena idea")

    # 3. Comprobamos la transición de estado
    assert mock_suggestion.status == "published"
    assert mock_suggestion.is_public is True
    assert mock_suggestion.moderation_note == "Buena idea"
    assert mock_suggestion.published_at is not None

def test_publish_already_published_raises_error(mock_service):
    # 1. Preparamos una sugerencia que YA está publicada
    mock_suggestion = Suggestion(id=2, status="published", is_public=True)
    mock_service.repo.session.get.return_value = mock_suggestion

    # 2. Comprobamos que intentar publicarla de nuevo lanza el Error 400
    with pytest.raises(HTTPException) as exc_info:
        mock_service.publish(id=2)
    
    assert exc_info.value.status_code == 400
    assert "ya está publicada" in exc_info.value.detail

def test_reject_suggestion(mock_service):
    # 1. Sugerencia pendiente
    mock_suggestion = Suggestion(id=3, status="pending", is_public=False)
    mock_service.repo.session.get.return_value = mock_suggestion

    # 2. Rechazamos
    mock_service.reject(id=3, note="No es viable")

    # 3. Validamos estados
    assert mock_suggestion.status == "rejected"
    assert mock_suggestion.is_public is False
    assert mock_suggestion.moderation_note == "No es viable"

def test_merge_suggestion_with_itself_raises_error(mock_service):
    # 1. Sugerencia origen y destino (intentamos fusionar la 4 con la 4)
    mock_suggestion = Suggestion(id=4, status="pending")
    
    # Configuramos el mock para que devuelva la misma sugerencia para ambos IDs
    mock_service.repo.session.get.return_value = mock_suggestion

    # 2. Comprobamos el error defensivo (Error 400)
    with pytest.raises(HTTPException) as exc_info:
        mock_service.merge(id=4, target_id=4)
        
    assert exc_info.value.status_code == 400
    assert "No puedes fusionar una sugerencia consigo misma" in exc_info.value.detail