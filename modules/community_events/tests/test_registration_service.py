import pytest
from app.core.exceptions import ValidationError
from modules.community_events.services.registration_service import RegistrationService
from modules.community_events.models.event import EventStatus

def test_registration_capacity_limit(db_session, create_user):
    """Prueba que no se puedan inscribir más personas del aforo permitido."""
    service = RegistrationService(db_session)
    
    # 1. Crear un evento con aforo 1
    event = service.create_model('community_events.event', {
        'title': 'Evento Test Aforo',
        'capacity_total': 1,
        'status': EventStatus.PUBLISHED,
        'is_public': True
    })
    
    # 2. Primera inscripción (debe funcionar)
    service.register_attendee(
        event_id=event.id,
        attendee_name="Asistente 1",
        attendee_email="test1@example.com"
    )
    
    # 3. Segunda inscripción (debe lanzar ValidationError)
    with pytest.raises(ValidationError) as excinfo:
        service.register_attendee(
            event_id=event.id,
            attendee_name="Asistente 2",
            attendee_email="test2@example.com"
        )
    
    assert "aforo completo" in str(excinfo.value).lower()

def test_registration_closed_event(db_session):
    """Prueba que no se pueda inscribir en un evento borrador."""
    service = RegistrationService(db_session)
    
    event = service.create_model('community_events.event', {
        'title': 'Evento Borrador',
        'status': EventStatus.DRAFT,
        'capacity_total': 10
    })
    
    with pytest.raises(ValidationError) as excinfo:
        service.register_attendee(
            event_id=event.id,
            attendee_name="Asistente",
            attendee_email="test@example.com"
        )
    assert "publicado" in str(excinfo.value).lower()