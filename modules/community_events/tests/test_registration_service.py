import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
# Importamos solo el servicio
from modules.community_events.services.registration import RegistrationService

@pytest.fixture
def mock_service():
    """Crea una instancia del servicio con una sesión de DB simulada."""
    mock_repo = MagicMock()
    mock_repo.session = MagicMock()
    # Le pasamos el mock_repo al servicio
    service = RegistrationService(mock_repo)
    return service

def test_registration_closed_event_raises_error(mock_service):
    """Prueba que no se pueda inscribir en un evento en borrador (draft)."""
    mock_event = MagicMock()
    mock_event.id = 1
    mock_event.status = "draft"
    mock_event.capacity_total = 2

    mock_service.repo.session.get.return_value = mock_event

    with pytest.raises(HTTPException) as exc_info:
        mock_service.create({
            "event_id": 1,
            "attendee_name": "Paco Pepe",
            "attendee_email": "paco@test.com"
        })

    assert exc_info.value.status_code == 400
    # Ajustamos para que coincida con tu mensaje: "Error: El evento 1 tiene estado 'draft'"
    assert "estado" in exc_info.value.detail.lower()
    assert "draft" in exc_info.value.detail.lower()

def test_registration_waitlist_logic(mock_service):
    """Prueba que la inscripción pase a waitlist si el aforo está completo."""
    # Creamos el evento simulado
    mock_event = MagicMock()
    mock_event.id = 1
    mock_event.status = "published"
    mock_event.capacity_total = 1
    
    # Simulamos que ya hay una persona confirmada
    # (Hacemos que el conteo de SQLAlchemy devuelva una lista con 1 elemento)
    mock_service.repo.session.scalars().all.return_value = [MagicMock()]
    mock_service.repo.session.get.return_value = mock_event

    data = {
        "event_id": 1,
        "attendee_name": "Juan",
        "attendee_email": "juan@test.com"
    }
    
    # Ejecutamos la lógica del servicio
    # (Capturamos el error de super().create porque no hay DB real, pero la lógica ya habrá corrido)
    try:
        mock_service.create(data)
    except:
        pass 

    # Verificamos que tu lógica cambió el estado a waitlist
    assert data["status"] == "waitlist"