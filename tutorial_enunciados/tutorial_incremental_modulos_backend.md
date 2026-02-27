# Tutorial incremental de creación de módulos backend
## Antes de empezar
## Este documento es una guía base para entender cómo funciona el sistema modular de Licium. No intentéis memorizarlo todo. La idea es ir paso a paso, probar cosas y entender qué está pasando. Si algo no funciona a la primera, es completamente normal. El uso de la IA es 

Este tutorial está pensado para alumnado en prácticas y personas nuevas en el
proyecto. La idea es aprender **cómo funciona el sistema modular de Licium**
mientras se implementa un módulo real, paso a paso.

El tutorial complementa:

- `docs/tech/como_crear_modulo_backend.md` (receta corta)
- `docs/tech/ui_catalogo.md` y `docs/tech/esquema_ui_admin.md` (UI admin)
- `docs/tech/seguridad_y_acl.md` (permisos)

## 1. Introducción y conceptos

## 1.1. Qué es un módulo backend

En Licium, un módulo backend es un paquete Python con:

- código (modelos, servicios, controladores opcionales)
- un `__manifest__.yaml` (dependencias + seeds + hooks)
- datos declarativos (vistas admin, menú, grupos, ACL, settings, etc.)

El backend monta APIs automáticamente a partir de los modelos registrados.

## 1.2. Flujo real de carga

Cuando instalas o actualizas un módulo (`python -m app.cli.module ...`), ocurre:

1. Se lee `__manifest__.yaml`.
2. Se importa el paquete Python (`modules.<technical_name>`).
3. Se registran modelos y servicios.
4. Se sincroniza el esquema de base de datos.
5. Se aplican seeds YAML/JSON (`data/`, `views/`, etc.).
6. Se ejecuta `post_init_hook` si existe.

Esto lo gestiona `backend/app/core/module_manager.py`.

## 1.3. Capas que debes diferenciar

1. Capa de datos:
`models/*.py` (SQLAlchemy + metadatos de campos para API/UI)

2. Capa de lógica:
`services/*.py` (CRUD personalizado + acciones con `@exposed_action`)

3. Capa de UI del admin (declarativa):
`views/views.yml`, `views/menu.yml`, opcional `data/ui_modules.yml`

4. Capa de seguridad:
`data/groups.yml` y `data/acl_rules.yml`

## 1.4. Seguridad: dos niveles distintos

1. Seguridad real (backend): ACL (`core.aclrule`) y grupos en
`@exposed_action(groups=[...])`.

2. Visibilidad en admin (frontend): `allowed_group_ext_ids` en `ui.action`,
o `groups` en acciones declaradas dentro de una vista.

Ocultar una acción en UI no sustituye una ACL.

## 1.5. Acciones de servicio con formulario automático

El admin puede mostrar un diálogo para ejecutar acciones `type: service`.

Si en el YAML no defines `params`, el frontend llama a `describe_action` y
construye el formulario desde la firma Python del método.

Ejemplo: si tu método recibe `close_note: str | None` y `make_public: bool`,
el diálogo mostrará esos campos automáticamente.

## 2. Módulo ejemplo incremental: `practice_checklist`

Objetivo funcional:

- Gestionar checklists internas con ítems.
- Permitir cerrar/reabrir checklists.
- Marcar ítems como hechos desde una acción de servicio.
- Exponer menú y vistas admin.
- Aplicar grupos y ACL.

## 2.1. Paso 0: estructura del módulo

En tiempo de ejecución, el backend descubre módulos en `backend/modules`.

Estructura mínima:

```text
backend/modules/practice_checklist/
  __init__.py
  __manifest__.yaml
  models/
    __init__.py
    checklist.py
  services/
    __init__.py
    checklist.py
  data/
    groups.yml
    acl_rules.yml
    ui_modules.yml
  views/
    views.yml
    menu.yml
```

Nota sobre este entorno:

- En este proyecto, `backend/modules/*` suele contener symlinks a `/opt/modules/*`.
- Para prácticas, puedes crear el módulo directamente en `backend/modules`.
- Si lo desarrollas en otro repo, crea un symlink dentro de `backend/modules`.

## 2.2. Paso 1: crear el manifest e imports

Archivo: `backend/modules/practice_checklist/__manifest__.yaml`

```yaml
name: Practice Checklist
technical_name: practice_checklist
version: 0.1
depends:
  - ui
data:
  - data/groups.yml
  - data/acl_rules.yml
  - data/ui_modules.yml
  - views/views.yml
  - views/menu.yml
migrations: {}
post_init_hook: null
```

Archivo: `backend/modules/practice_checklist/__init__.py`

```python
from . import models  # noqa: F401
from . import services  # noqa: F401
```

Archivo: `backend/modules/practice_checklist/models/__init__.py`

```python
from .checklist import PracticeChecklist, PracticeChecklistItem  # noqa: F401
```

Archivo: `backend/modules/practice_checklist/services/__init__.py`

```python
from .checklist import PracticeChecklistService, PracticeChecklistItemService  # noqa: F401
```

## Sobre los modelos. Aquí empieza la parte importante: definir bien los datos. Antes de escribir código, pensad qué representa cada modelo y qué relación tiene con los demás. Un modelo mal pensado os dará problemas más adelante.

## 2.3. Paso 2: primer modelo (`checklist`)

Archivo: `backend/modules/practice_checklist/models/checklist.py`

```python
from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship
from app.core.base import Base
from app.core.fields import field


class PracticeChecklist(Base):
    __tablename__ = "practice_checklist"
    __abstract__ = False
    __model__ = "checklist"
    __service__ = "modules.practice_checklist.services.checklist.PracticeChecklistService"

    __selector_config__ = {
        "label_field": "name",
        "search_fields": ["name", "status", "description"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "name", "label": "Checklist"},
            {"field": "status", "label": "Estado"},
            {"field": "is_public", "label": "Público"},
        ],
    }

    name = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Checklist", "en": "Checklist"}},
    )
    description = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Descripción", "en": "Description"}},
    )
    status = field(
        String(20),
        required=True,
        public=True,
        editable=True,
        default="draft",
        info={
            "label": {"es": "Estado", "en": "Status"},
            "choices": [
                {"label": "Draft", "value": "draft"},
                {"label": "Open", "value": "open"},
                {"label": "Closed", "value": "closed"},
            ],
        },
    )
    is_public = field(
        Boolean,
        required=True,
        public=True,
        editable=True,
        default=False,
        info={"label": {"es": "Público", "en": "Public"}},
    )
    owner_id = field(
        Integer,
        ForeignKey("core_user.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Responsable", "en": "Owner"}},
    )
    owner = relationship(
        "User",
        foreign_keys=lambda: [PracticeChecklist.owner_id],
        info={"public": True, "recursive": False, "editable": True},
    )
    closed_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Cerrado en", "en": "Closed at"}},
    )


class PracticeChecklistItem(Base):
    __tablename__ = "practice_checklist_item"
    __abstract__ = False
    __model__ = "checklist_item"
    __service__ = "modules.practice_checklist.services.checklist.PracticeChecklistItemService"

    __selector_config__ = {
        "label_field": "title",
        "search_fields": ["title", "note"],
        "columns": [
            {"field": "id", "label": "ID"},
            {"field": "checklist", "label": "Checklist"},
            {"field": "title", "label": "Ítem"},
            {"field": "is_done", "label": "Hecho"},
        ],
    }

    checklist_id = field(
        Integer,
        ForeignKey("practice_checklist.id", ondelete="CASCADE"),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Checklist", "en": "Checklist"}},
    )
    checklist = relationship(
        "modules.practice_checklist.models.checklist.PracticeChecklist",
        foreign_keys=lambda: [PracticeChecklistItem.checklist_id],
        backref=backref("items", cascade="all, delete-orphan"),
        info={"public": True, "recursive": False, "editable": True},
    )
    title = field(
        String(180),
        required=True,
        public=True,
        editable=True,
        info={"label": {"es": "Ítem", "en": "Item"}},
    )
    note = field(
        Text,
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Nota", "en": "Note"}},
    )
    assigned_user_id = field(
        Integer,
        ForeignKey("core_user.id"),
        required=False,
        public=True,
        editable=True,
        info={"label": {"es": "Asignado a", "en": "Assigned to"}},
    )
    assigned_user = relationship(
        "User",
        foreign_keys=lambda: [PracticeChecklistItem.assigned_user_id],
        info={"public": True, "recursive": False, "editable": True},
    )
    is_done = field(
        Boolean,
        required=True,
        public=True,
        editable=True,
        default=False,
        info={"label": {"es": "Hecho", "en": "Done"}},
    )
    done_at = field(
        DateTime(timezone=True),
        required=False,
        public=True,
        editable=False,
        info={"label": {"es": "Hecho en", "en": "Done at"}},
    )
```

Con esto ya tienes el CRUD automático para:

- `/api/practice_checklist/checklist`
- `/api/practice_checklist/checklist_item`


## 2.4. Paso 3: servicios y acciones
## Aquí es donde empezamos a salir del CRUD automático. No todo se resuelve creando campos: muchas veces la lógica real está en los servicios. Pensad siempre: ¿qué debería poder hacerse y en qué condiciones?

Archivo: `backend/modules/practice_checklist/services/checklist.py`

```python
from __future__ import annotations

import datetime as dt

from fastapi import HTTPException

from app.core.base import BaseService
from app.core.context import get_current_user_id
from app.core.serializer import serialize
from app.core.services import exposed_action

from ..models import PracticeChecklist, PracticeChecklistItem


class PracticeChecklistService(BaseService):
    from ..models import PracticeChecklist


    def create(self, obj):  # type: ignore[override]
        if not isinstance(obj, dict):
            return super().create(obj)
        payload = dict(obj)
        if not payload.get("owner_id"):
            payload["owner_id"] = get_current_user_id()
        if not payload.get("status"):
            payload["status"] = "open"
        return super().create(payload)

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def close(self, id: int, close_note: str | None = None, make_public: bool = False) -> dict:
        rec = self.repo.session.get(PracticeChecklist, int(id))
        if rec is None:
            raise HTTPException(404, "Checklist not found")
        rec.status = "closed"
        rec.is_public = bool(make_public)
        rec.closed_at = dt.datetime.now(dt.timezone.utc)
        if close_note:
            base = (rec.description or "").strip()
            rec.description = f"{base}\n\n[Cierre] {close_note}".strip()
        self.repo.session.add(rec)
        self.repo.session.commit()
        self.repo.session.refresh(rec)
        return serialize(rec)

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def reopen(self, id: int) -> dict:
        rec = self.repo.session.get(PracticeChecklist, int(id))
        if rec is None:
            raise HTTPException(404, "Checklist not found")
        rec.status = "open"
        rec.closed_at = None
        self.repo.session.add(rec)
        self.repo.session.commit()
        self.repo.session.refresh(rec)
        return serialize(rec)


class PracticeChecklistItemService(BaseService):
    from ..models import PracticeChecklistItem

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def set_done(self, id: int, done: bool = True, note: str | None = None) -> dict:
        item = self.repo.session.get(PracticeChecklistItem, int(id))
        if item is None:
            raise HTTPException(404, "Checklist item not found")
        item.is_done = bool(done)
        item.done_at = dt.datetime.now(dt.timezone.utc) if done else None
        if note:
            base = (item.note or "").strip()
            item.note = f"{base}\n\n[Estado] {note}".strip()
        self.repo.session.add(item)
        self.repo.session.commit()
        self.repo.session.refresh(item)
        return serialize(item)
```

Punto didáctico importante:

- `close(...)` y `set_done(...)` tienen parámetros tipados.
- Si los llamas desde una acción `type: service` sin `params` en YAML, el admin
  construirá el diálogo automáticamente.

## 2.5. Paso 4: grupos y ACL
## Muy importante: seguridad. Que algo se vea en el admin no significa que esté permitido. La seguridad real está en las ACL. Si alguna vez algo “se ve” pero devuelve 403, casi seguro que es un tema de permisos.

Archivo: `backend/modules/practice_checklist/data/groups.yml`

```yaml
- model: core.group
  ext_id: practice_checklist_group_reader
  fields:
    name: "Practice checklist - Lectura"
    parent_id.ext_id: core.core_group_internal_user

- model: core.group
  ext_id: practice_checklist_group_manager
  fields:
    name: "Practice checklist - Gestión"
    parent_id.ext_id: practice_checklist_group_reader
```

Archivo: `backend/modules/practice_checklist/data/acl_rules.yml`

```yaml
- model: core.aclrule
  ext_id: practice_checklist_acl_reader_read
  fields:
    model_key: "practice_checklist.*"
    group_id.ext_id: practice_checklist_group_reader
    perm_read: true

- model: core.aclrule
  ext_id: practice_checklist_acl_manager_all
  fields:
    model_key: "practice_checklist.*"
    group_id.ext_id: practice_checklist_group_manager
    perm_read: true
    perm_write: true
    perm_create: true
    perm_delete: true

- model: core.aclrule
  ext_id: practice_checklist_acl_public_read_closed
  fields:
    model_key: "practice_checklist.checklist"
    group_id.ext_id: core.core_group_public
    perm_read: true
    domain:
      - { field: "is_public", operator: "=", value: true }
      - { field: "status", operator: "=", value: "closed" }
```

Con esto practicas:

- ACL por wildcard (`practice_checklist.*`)
- ACL pública con `domain` (caso real)

## 2.6. Paso 5: módulo UI opcional

Archivo: `backend/modules/practice_checklist/data/ui_modules.yml`

```yaml
- model: ui.uimodule
  ext_id: practice_checklist_ui_module
  fields:
    slug: practice-checklist
    name: Practice Checklist
    description: "Módulo de ejemplo para prácticas de backend"
    active: true
```

No es obligatorio para funcionar, pero ordena el catálogo UI.

## 2.7. Paso 6: vistas admin (`views.yml`)

Archivo: `backend/modules/practice_checklist/views/views.yml`

```yaml
- model: ui.view
  ext_id: practice_checklist_view_checklist_list
  fields:
    name: "practice_checklist.checklist - Lista"
    title:
      $fallback: "Checklists - Lista"
    model_key: practice_checklist.checklist
    type_id.ext_id: ui.ui_view_type_list
    definition:
      columns:
        - { field: id, label: ID, width: 70 }
        - { field: name, label: Checklist, sortable: true }
        - { field: status, label: Estado, chip: true }
        - { field: owner_id, label: Responsable }
        - { field: is_public, label: Público, width: 90 }
        - { field: closed_at, label: Cerrado en }
      actions:
        - { name: new, type: create, icon: mdi-plus, label: "Nuevo" }
        - { name: edit, type: update, icon: mdi-pencil, label: "Editar" }
        - { name: delete, type: delete, icon: mdi-delete, label: "Borrar" }
      row_actions:
        - key: close
          type: service
          label: "Cerrar"
          icon: mdi-check
          method: close
          model_key: practice_checklist.checklist
          groups: [practice_checklist_group_manager, core_group_superadmin]
          confirm:
            text: "¿Cerrar checklist?"
        - key: reopen
          type: service
          label: "Reabrir"
          icon: mdi-lock-open-variant-outline
          method: reopen
          model_key: practice_checklist.checklist
          groups: [practice_checklist_group_manager, core_group_superadmin]
          confirm:
            text: "¿Reabrir checklist?"

- model: ui.view
  ext_id: practice_checklist_view_checklist_form
  fields:
    name: "practice_checklist.checklist - Formulario"
    title:
      $fallback: "Checklist - Formulario"
    model_key: practice_checklist.checklist
    type_id.ext_id: ui.ui_view_type_form
    definition:
      groups:
        - label: Básico
          fields: [name, status, owner_id, is_public]
        - label: Descripción
          fields: [description]
        - label: Auditoría
          fields: [closed_at]
      form_actions:
        - key: close
          type: service
          label: "Cerrar"
          icon: mdi-check
          method: close
          groups: [practice_checklist_group_manager, core_group_superadmin]
          confirm:
            text: "¿Cerrar checklist?"
        - key: reopen
          type: service
          label: "Reabrir"
          icon: mdi-lock-open-variant-outline
          method: reopen
          groups: [practice_checklist_group_manager, core_group_superadmin]
          confirm:
            text: "¿Reabrir checklist?"

- model: ui.view
  ext_id: practice_checklist_view_item_list
  fields:
    name: "practice_checklist.checklist_item - Lista"
    title:
      $fallback: "Ítems - Lista"
    model_key: practice_checklist.checklist_item
    type_id.ext_id: ui.ui_view_type_list
    definition:
      columns:
        - { field: id, label: ID, width: 70 }
        - { field: checklist, label: Checklist }
        - { field: title, label: Ítem, sortable: true }
        - { field: assigned_user_id, label: Asignado }
        - { field: is_done, label: Hecho, chip: true }
        - { field: done_at, label: Hecho en }
      actions:
        - { name: new, type: create, icon: mdi-plus, label: "Nuevo" }
        - { name: edit, type: update, icon: mdi-pencil, label: "Editar" }
        - { name: delete, type: delete, icon: mdi-delete, label: "Borrar" }
      row_actions:
        - key: mark_done
          type: service
          label: "Marcar hecho"
          icon: mdi-check
          method: set_done
          model_key: practice_checklist.checklist_item
          groups: [practice_checklist_group_manager, core_group_superadmin]
        - key: mark_pending
          type: service
          label: "Marcar pendiente"
          icon: mdi-undo
          method: set_done
          model_key: practice_checklist.checklist_item
          groups: [practice_checklist_group_manager, core_group_superadmin]
          params:
            - name: done
              label: Hecho
              type: boolean
              default: false

- model: ui.view
  ext_id: practice_checklist_view_item_form
  fields:
    name: "practice_checklist.checklist_item - Formulario"
    title:
      $fallback: "Ítem - Formulario"
    model_key: practice_checklist.checklist_item
    type_id.ext_id: ui.ui_view_type_form
    definition:
      groups:
        - label: Básico
          fields: [checklist_id, title, assigned_user_id, is_done]
        - label: Nota
          fields: [note]
        - label: Auditoría
          fields: [done_at]
      form_actions:
        - key: set_done
          type: service
          label: "Actualizar estado"
          icon: mdi-check-decagram
          method: set_done
          groups: [practice_checklist_group_manager, core_group_superadmin]
```

Observa que:

- En varias acciones no definimos `params`: se autodescriben por firma Python.
- En `mark_pending` si fijamos `params` para forzar un valor por defecto.

## 2.8. Paso 7: acciones y menú (`menu.yml`)

Archivo: `backend/modules/practice_checklist/views/menu.yml`

```yaml
- model: ui.menuitem
  ext_id: practice_checklist_menu_root
  fields:
    title: "Practice"
    icon: mdi-format-list-checks
    color_primary: "#2F5A77"
    color_secondary: "#2F5A7766"

- model: ui.action
  ext_id: practice_checklist_action_checklists
  fields:
    name: "Practice - Checklists"
    title:
      $fallback: "Checklists"
    route: practice/checklists
    model_key: practice_checklist.checklist
    model_path: "practice_checklist/checklist"
    menu: true
    context:
      allowed_group_ext_ids:
        - practice_checklist_group_reader
        - practice_checklist_group_manager
        - core_group_superadmin
    default_multi_read_view_id.ext_id: practice_checklist_view_checklist_list
    default_single_edit_view_id.ext_id: practice_checklist_view_checklist_form
    views.ext_id:
      - practice_checklist_view_checklist_list
      - practice_checklist_view_checklist_form

- model: ui.menuitem
  ext_id: practice_checklist_menu_checklists
  fields:
    title: "Checklists"
    icon: mdi-clipboard-text-outline
    parent_id.ext_id: practice_checklist_menu_root
    action_id.ext_id: practice_checklist_action_checklists

- model: ui.action
  ext_id: practice_checklist_action_items
  fields:
    name: "Practice - Items"
    title:
      $fallback: "Ítems"
    route: practice/checklist-items
    model_key: practice_checklist.checklist_item
    model_path: "practice_checklist/checklist_item"
    menu: true
    context:
      allowed_group_ext_ids:
        - practice_checklist_group_reader
        - practice_checklist_group_manager
        - core_group_superadmin
    default_multi_read_view_id.ext_id: practice_checklist_view_item_list
    default_single_edit_view_id.ext_id: practice_checklist_view_item_form
    views.ext_id:
      - practice_checklist_view_item_list
      - practice_checklist_view_item_form

- model: ui.menuitem
  ext_id: practice_checklist_menu_items
  fields:
    title: "Ítems"
    icon: mdi-format-list-bulleted
    parent_id.ext_id: practice_checklist_menu_root
    action_id.ext_id: practice_checklist_action_items
```

## 2.9. Paso 8: instalar y actualizar

Desde `/opt/backend`:

```bash
python -m app.cli.module install modules/practice_checklist -y
python -m app.cli.module update modules/practice_checklist -y
```

Cuando cambies seeds o código del módulo:

```bash
python -m app.cli.module update modules/practice_checklist -y
```

Si quieres ver DDL sin aplicar:

```bash
python -m app.cli.module update modules/practice_checklist --dry-run -y
```

## 2.10. Paso 9: validación funcional

Checklist de validación para alumnado:

1. API:
   - CRUD de `/api/practice_checklist/checklist` funciona.
   - CRUD de `/api/practice_checklist/checklist_item` funciona.
2. Admin:
   - Aparece el menú "Practice".
   - Se ven listas y formularios.
3. Acciones:
   - `close` y `reopen` ejecutan correctamente.
   - `set_done` abre un diálogo con parámetros.
4. Seguridad:
   - Reader: solo lectura.
   - Manager: crear/editar/borrar + acciones.
   - Público: solo lee checklists cerradas y públicas (si se expone endpoint).

## 3. Mejoras incrementales recomendadas

Una vez superado el baseline, para subir dificultad:

1. Añadir `bulk_actions` en lista (`set_done` masivo).
2. Añadir `settings` del módulo (por ejemplo, política de cierre automático).
3. Añadir `i18n/es.yml` y `i18n/en.yml` para títulos/labels.
4. Añadir tests unitarios de servicio (acciones `close`, `set_done`).
5. Añadir un `service_override` si necesitas extender comportamiento de otro
   módulo sin tocar su código fuente.

## 4. Errores frecuentes en prácticas

## Os dejamos un pequeño listado con algunos errores comunes que seguramente os ocurran durante el desarrollo. Son los más típicos cuando se empieza a trabajar con módulos. Si os ocurre alguno distinto, primero intentad entender el error y revisad lo que habéis tocado.Podéis preguntar a vuestros compañeros, y si entre todos no encontráis la solución, entonces preguntad a los tutores 

1. El módulo no aparece:
   - falta import en `__init__.py`
   - `technical_name` no coincide con carpeta/import

2. El modelo existe pero no hay menú:
   - faltan `ui.action` y `ui.menuitem` en seeds

3. La acción no aparece:
   - grupo no incluido en `groups`/`allowed_group_ext_ids`
   - la acción existe en backend pero no en YAML de vista

4. Devuelve 403 aunque "se ve" en UI:
   - ACL de backend no permite la operación


## 5. Ruta didáctica sugerida (2-3 semanas)

## Nota importante. Esta planificación es orientativa. No tenéis que tomarla al pie de la letra. Cada equipo avanza a un ritmo distinto y es completamente normal que algunas partes os lleven más tiempo que otras. 
# Lo importante no es cumplir exactamente las semanas, sino entender bien cada bloque antes de pasar al siguiente. Si una fase necesita más tiempo, lo ajustamos. Preferimos que algo esté bien entendido y bien hecho, a que esté simplemente “terminado”.

1. Semana 1:
   estructura, manifest, modelos y CRUD.
2. Semana 2:
   servicios, acciones y UI admin.
3. Semana 3:
   seguridad fina (ACL domain), tests y documentación final.

Con esta secuencia, el alumnado practica el stack completo sin saltos.
