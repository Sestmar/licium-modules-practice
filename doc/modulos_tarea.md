# Tutorial de módulos backend (niveles 2-4)
## Cómo usar este documento: Este documento no es un tutorial paso a paso como el anterior. Aquí ya no vamos guiados línea por línea, ahora toca aplicar lo aprendido en módulos más reales.

## Cada nivel es un módulo diferente y más complejo que el anterior. No se trata de correr para terminarlo, sino de diseñarlo bien.

# IMPORTANTE: Si todavía no os sentís cómodos creando modelos, servicios y configurando ACL básicas,os recomendamos repasar el documento anterior. Estos niveles ya asumen que sabéis cómo funciona el sistema modular.

Este documento continúa el tutorial base:

- `docs/tech/tutorial_modulo_backend_incremental.md`

Aquí se proponen tres módulos con dificultad creciente para prácticas:

1. Nivel 2: `asset_lending` (préstamo de recursos)
2. Nivel 3: `feedback_moderation` (sugerencias y moderación)
3. Nivel 4: `community_events` (eventos publicables para la comunidad)

El objetivo es que el alumnado practique todo el stack:

- modelos
- servicios con acciones
- vistas admin automáticas (`ui.view`, `ui.action`, `ui.menuitem`)
- seguridad (`groups`, `acl_rules`, domains)
- ajustes (settings) del módulo

## 1. Requisitos previos

Antes de empezar estos niveles, recomendamos que el equipo ya haya completado:

1. módulo simple con CRUD y menú admin
2. al menos una acción `type: service`
3. ACL básica por grupo

## 2. Nivel 2: `asset_lending`

## 2.1. Objetivo funcional

Gestionar préstamos de equipamiento interno:

- inventario de recursos (portátiles, cámaras, micrófonos, etc.)
- préstamos con fecha de salida/devolución
- estados operativos del recurso

## 2.2. Modelos recomendados

1. `asset_lending.location`
Campos mínimos:
`name`, `code`, `is_active`

2. `asset_lending.asset`
Campos mínimos:
`name`, `asset_code`, `status` (`available`, `loaned`, `maintenance`),
`location_id`, `responsible_user_id`, `notes`

3. `asset_lending.loan`
Campos mínimos:
`asset_id`, `borrower_user_id`, `checkout_at`, `due_at`, `returned_at`,
`status` (`open`, `returned`, `overdue`), `checkout_note`, `return_note`

## 2.3. Servicios y acciones

Servicio principal: `AssetLoanService`

Acciones recomendadas:

1. `checkout(loan_id | asset_id, borrower_user_id, due_at, note)`
   - valida que el recurso esté `available`
   - marca `asset.status = loaned`
   - deja el préstamo en `open`

2. `return_asset(loan_id, note)`
   - valida que el préstamo esté `open`
   - marca `returned_at` y `status = returned`
   - marca `asset.status = available`

3. `mark_maintenance(asset_id, note)`
   - mueve recurso a estado `maintenance`

4. `release_maintenance(asset_id)`
   - vuelve a `available`

## 2.4. UI admin

`views/views.yml`:

1. lista/form de `asset`
2. lista/form de `loan`
3. lista/form de `location`

`views/menu.yml`:

1. menú raíz "Assets"
2. submenús "Recursos", "Préstamos", "Ubicaciones"

Recomendación didáctica:

- usar `row_actions` de tipo `service` en `loan` para devolver recurso
- usar `chip` en columnas de estado

## 2.5. Seguridad

Grupos:

1. `asset_lending_group_reader`
2. `asset_lending_group_manager`

ACL:

1. reader: `perm_read` en `asset_lending.*`
2. manager: `perm_read/write/create/delete` en `asset_lending.*`

Opcional (más realista):

- dominio para que un grupo "técnico" solo modifique recursos de su `location_id`

## 2.6. Entregables del nivel 2

1. módulo instalable por CLI
2. flujo completo checkout/return probado
3. vistas admin funcionales
4. ACL separada por lector/gestor

## 3. Nivel 3: `feedback_moderation`

## 3.1. Objetivo funcional

Recoger sugerencias/comentarios y moderarlos desde admin.

Caso real:

- usuarios públicos envían sugerencias
- moderadores publican o rechazan
- solo el contenido publicado se expone en lectura pública

## 3.2. Modelos recomendados

1. `feedback_moderation.suggestion`
Campos:
`title`, `content`, `status` (`pending`, `published`, `rejected`, `merged`),
`author_email`, `author_name`, `is_public`, `moderation_note`,
`published_at`, `reviewed_by_id`

2. `feedback_moderation.comment`
Campos:
`suggestion_id`, `content`, `status` (`pending`, `published`, `rejected`),
`author_email`, `is_public`, `published_at`

3. `feedback_moderation.tag`
Campos:
`name`, `slug`, `color`
Relación M2M sugerencia-etiqueta.

## 3.3. Servicios y acciones

Servicio principal: `SuggestionService`

Acciones recomendadas:

1. `publish(id, note=None, pin=False)`
2. `reject(id, note)`
3. `merge(id, target_id, note=None)`
4. `reopen(id)`

Servicio secundario: `CommentService`

Acciones:

1. `publish_comment(id, note=None)`
2. `reject_comment(id, note)`

## 3.4. UI admin

Vistas:

1. lista/form de sugerencias con filtros por `status`
2. lista/form de comentarios
3. lista/form de tags

Acciones en formulario:

1. botones `publish`, `reject`, `merge`
2. parámetro `target_id` en `merge` (selector de relación)

## 3.5. Seguridad

Grupos:

1. `feedback_group_moderator`
2. `feedback_group_viewer`

ACL sugeridas:

1. público:
   - `perm_create` en `feedback_moderation.suggestion`
   - `perm_create` en `feedback_moderation.comment`
   - `perm_read` en `feedback_moderation.suggestion` con domain:
     `status = published` e `is_public = true`
   - `perm_read` en `feedback_moderation.comment` con domain equivalente

2. moderador:
   - CRUD total en `feedback_moderation.*`

## 3.6. Entregables del nivel 3

1. flujo de moderación extremo a extremo
2. ACL pública con domain
3. acciones de estado con formulario automático
4. pruebas unitarias de transición de estado

## 4. Nivel 4: `community_events` (publicable community)

## 4.1. Objetivo funcional

Módulo útil para publicar en la comunidad:

- gestion de eventos
- sesiones internas por evento
- inscripciones
- control de asistencia

## 4.2. Modelos recomendados

1. `community_events.event`
Campos:
`title`, `slug`, `summary`, `description`, `status`
(`draft`, `published`, `closed`, `cancelled`), `start_at`, `end_at`,
`location`, `capacity_total`, `is_public`, `organizer_user_id`

2. `community_events.session`
Campos:
`event_id`, `title`, `start_at`, `end_at`, `speaker_name`, `room`,
`capacity`, `status`

3. `community_events.registration`
Campos:
`event_id`, `session_id` (opcional), `attendee_name`, `attendee_email`,
`attendee_user_id` (opcional), `status`
(`pending`, `confirmed`, `waitlist`, `cancelled`), `registered_at`,
`checkin_at`, `notes`

4. `community_events.checkin` (opcional)
Campos:
`registration_id`, `checked_by_user_id`, `checked_at`, `source`

## 4.3. Servicios y acciones

Servicio `EventService`:

1. `publish_event(id, note=None)`
2. `close_registration(id, reason=None)`
3. `cancel_event(id, reason)`
4. `reopen_event(id)`

Servicio `RegistrationService`:

1. `register(event_id, attendee_name, attendee_email, session_id=None)`
2. `confirm(id, note=None)`
3. `move_waitlist(id, note=None)`
4. `checkin(id, source="manual")`
5. `bulk_checkin(ids)` (acción masiva)

Servicio `ReminderService` (opcional):

1. `send_reminder(event_id, template_id=None, dry_run=False)`

## 4.4. UI admin

1. menú raíz "Eventos"
2. acciones para `event`, `session`, `registration`
3. vistas con:
   - filtros guardados por estado
   - `bulk_actions` en registros (confirmar/checkin)
   - `row_actions` para flujos de estado
4. `buttonbox` en evento:
   - contador de registros
   - acceso directo a lista filtrada por evento

## 4.5. Seguridad

Grupos:

1. `community_events_group_staff`
2. `community_events_group_viewer`

ACL recomendadas:

1. público:
   - `perm_read` en `community_events.event` con domain:
     `status = published` e `is_public = true`
   - `perm_read` en `community_events.session` si evento publicado
   - `perm_create` en `community_events.registration`
   - `perm_read` de su propia inscripción (si hay identidad de usuario)

2. staff:
   - CRUD total en `community_events.*`

## 4.6. Settings recomendados

Añadir en `data/settings.yml`:

1. `community_events.allow_waitlist` (bool)
2. `community_events.default_capacity` (int)
3. `community_events.auto_confirm` (bool)
4. `community_events.reminder_hours_before` (int)

## 4.7. Criterios para publicar como community

1. nombre técnico estable y versionado semántico
2. seeds idempotentes (`ext_id` coherentes)
3. ACL segura por defecto
4. tests mínimos de servicios críticos
5. documentación de instalación y uso

## 5. Plan de trabajo sugerido (8-10 semanas)

1. Semanas 1-3: nivel 2 (`asset_lending`)
2. Semanas 4-6: nivel 3 (`feedback_moderation`)
3. Semanas 7-10: nivel 4 (`community_events`)

Cada nivel debe cerrar con:

1. demo funcional en admin
2. validación de ACL
3. retrospectiva técnica (qué simplificar/mejorar)

## Recordatorio final: No intentéis impresionar con cantidad de código. Nos interesa más la coherencia, claridad, seguridad, etc...
# Si algo funciona pero es confuso o inseguro, lo revisaremos.

## 6. Consejos de tutorización

1. pedir commits pequeños por fase (modelos, servicios, UI, ACL)
2. revisar primero seguridad y estados, luego estilo
3. evitar mezclar en una misma PR cambios de tres niveles
4. convertir errores reales en "checklist de aprendizaje"

Con esta ruta, los módulos 2-4 no solo sirven para prácticas: también dejan
bases reutilizables para módulos publicables en la comunidad.
