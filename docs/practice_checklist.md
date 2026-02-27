# 📋 Practice Checklist — Módulo Nivel 1

> **Módulo introductorio** que implementa un gestor de tareas y checklists. Primer contacto con las capas de datos, lógica de negocio, vistas declarativas y seguridad básica del framework Licium.

---

## Índice

- [Objetivo](#objetivo)
- [Modelos de Datos](#modelos-de-datos)
- [Lógica de Negocio (Services)](#lógica-de-negocio-services)
- [Vistas Declarativas (YAML)](#vistas-declarativas-yaml)
- [Seguridad y Permisos](#seguridad-y-permisos)
- [Hitos Técnicos](#hitos-técnicos)

---

## Objetivo

Construir un módulo funcional de gestión de **checklists** (listas de verificación) con ítems asignables, que permita:

- Crear, editar y eliminar checklists y sus ítems.
- Cerrar y reabrir checklists con notas de cierre.
- Marcar ítems como completados de forma individual o masiva.
- Aplicar seguridad por grupos con permisos diferenciados de lectura y escritura.

---

## Modelos de Datos

El módulo define dos tablas con una relación de agregación (`1:N` con `CASCADE`):

### `PracticeChecklist`

Tabla principal que representa una lista de verificación.

```python
class PracticeChecklist(Base):
    __tablename__ = "practice_checklist"
    __model__ = "checklist"

    name        = field(String(180), required=True, ...)
    description = field(Text, ...)
    status      = field(String(20), default="draft", ...)   # draft | open | closed
    is_public   = field(Boolean, default=False, ...)
    owner_id    = field(Uuid, ForeignKey("core_user.id"), ...)
    closed_at   = field(DateTime(timezone=True), editable=False, ...)
```

| Campo | Tipo | Propósito |
|-------|------|-----------|
| `name` | `String(180)` | Nombre descriptivo del checklist |
| `status` | `String(20)` | Control de ciclo de vida: `draft` → `open` → `closed` |
| `is_public` | `Boolean` | Visibilidad para usuarios sin permisos explícitos |
| `owner_id` | `FK → core_user` | Responsable asignado automáticamente al crear |
| `closed_at` | `DateTime` | Marca temporal de cierre (no editable manualmente) |

### `PracticeChecklistItem`

Ítems subordinados a un checklist, con soporte para asignación individual.

```python
class PracticeChecklistItem(Base):
    __tablename__ = "practice_checklist_item"
    __model__ = "checklist_item"

    checklist_id    = field(Integer, ForeignKey("practice_checklist.id", ondelete="CASCADE"), ...)
    title           = field(String(180), required=True, ...)
    note            = field(Text, ...)
    assigned_user_id = field(Uuid, ForeignKey("core_user.id"), ...)
    is_done         = field(Boolean, default=False, ...)
    done_at         = field(DateTime(timezone=True), editable=False, ...)
```

La relación de integridad referencial se establece con `ondelete="CASCADE"`, de manera que al eliminar un checklist **se eliminan automáticamente todos sus ítems asociados**.

---

## Lógica de Negocio (Services)

### `PracticeChecklistService`

| Acción | Decorador | Descripción |
|--------|-----------|-------------|
| `close()` | `@exposed_action("write")` | Cierra el checklist → establece `status="closed"`, registra `closed_at` y opcionalmente añade una nota de cierre y marca como público |
| `reopen()` | `@exposed_action("write")` | Reabre un checklist cerrado → restaura `status="open"` y limpia `closed_at` |

El método `create()` se sobreescribe para asignar automáticamente el `owner_id` del usuario autenticado y establecer el estado inicial como `"open"`.

### `PracticeChecklistItemService`

| Acción | Decorador | Descripción |
|--------|-----------|-------------|
| `set_done()` | `@exposed_action("write")` | Marca/desmarca un ítem como completado, registra `done_at` y permite agregar una nota |
| `bulk_set_done()` | `@exposed_action("write")` | Operación masiva: recibe una lista de IDs y actualiza todos en una sola transacción |

#### Ejemplo: Decorador `@exposed_action`

El decorador `@exposed_action` es la pieza central para exponer lógica como botones en la UI. Define el nivel de permiso (`"write"`) y los grupos autorizados:

```python
@exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
def close(self, id: int, close_note: str | None = None, make_public: bool = False) -> dict:
    # El tipado de los parámetros genera automáticamente un diálogo en el frontend
    ...
```

---

## Vistas Declarativas (YAML)

El frontend de Licium genera las interfaces completas a partir de la definición YAML. No se escribe HTML, CSS ni JavaScript.

### Enlace entre vista y modelo: `model_key`

El atributo `model_key` es el **vínculo crítico** entre una vista YAML y un modelo Python. Sigue el formato `<technical_name>.<__model__>`:

```yaml
model_key: practice_checklist.checklist        # → PracticeChecklist
model_key: practice_checklist.checklist_item   # → PracticeChecklistItem
```

### Vista de Lista (`ui_view_type_list`)

Define las columnas visibles, acciones globales (crear, editar, eliminar) y acciones por fila:

```yaml
- model: ui.view
  ext_id: practice_checklist_view_checklist_list
  fields:
    model_key: practice_checklist.checklist
    type_id.ext_id: ui.ui_view_type_list
    definition:
      columns:
        - { field: id, label: ID, width: 70 }
        - { field: name, label: Checklist, sortable: true }
        - { field: status, label: Estado, chip: true }
      row_actions:
        - key: close
          type: service
          method: close                # ← Llama a PracticeChecklistService.close()
          model_key: practice_checklist.checklist
          groups: [practice_checklist_group_manager, core_group_superadmin]
```

### Vista de Formulario (`ui_view_type_form`)

Organiza los campos en grupos lógicos con pestañas:

```yaml
- model: ui.view
  ext_id: practice_checklist_view_checklist_form
  fields:
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
```

### Menú de Navegación (`menu.yml`)

El menú conecta la barra de navegación con las vistas mediante **acciones** (`ui.action`):

```yaml
# Definición de la acción (ruta + vistas asociadas)
- model: ui.action
  ext_id: practice_checklist_action_checklists
  fields:
    route: practice/checklists
    model_key: practice_checklist.checklist
    default_multi_read_view_id.ext_id: practice_checklist_view_checklist_list
    default_single_edit_view_id.ext_id: practice_checklist_view_checklist_form

# Entrada visible en el menú lateral
- model: ui.menuitem
  ext_id: practice_checklist_menu_checklists
  fields:
    title: "Checklists"
    icon: mdi-clipboard-text-outline
    parent_id.ext_id: practice_checklist_menu_root
    action_id.ext_id: practice_checklist_action_checklists
```

### Acciones masivas (`bulk_actions`)

La vista de ítems incluye una acción masiva que permite seleccionar múltiples registros y actuar sobre todos a la vez:

```yaml
bulk_actions:
  - key: bulk_mark_done
    type: service
    label: "Marcar selección como hecha"
    method: bulk_set_done
    model_key: practice_checklist.checklist_item
    confirm:
      text: "¿Estás seguro de marcar estas tareas como hechas?"
```

---

## Seguridad y Permisos

### Grupos

El módulo define dos grupos con herencia jerárquica:

```yaml
# El lector hereda de core_group_internal_user
- model: core.group
  ext_id: practice_checklist_group_reader
  fields:
    name: "Practice checklist - Lectura"
    parent_id.ext_id: core.core_group_internal_user

# El gestor hereda del lector (hereda permisos de lectura)
- model: core.group
  ext_id: practice_checklist_group_manager
  fields:
    name: "Practice checklist - Gestión"
    parent_id.ext_id: practice_checklist_group_reader
```

### Reglas ACL

| Regla | Grupo | Modelo | Permisos | Dominio |
|-------|-------|--------|----------|---------|
| `acl_reader_read` | Lector | `practice_checklist.*` | Lectura | — |
| `acl_manager_all` | Gestor | `practice_checklist.*` | CRUD completo | — |
| `acl_public_read_closed` | Público | `practice_checklist.checklist` | Lectura | `is_public = true` AND `status = "closed"` |

La regla `acl_public_read_closed` es un primer ejemplo de **filtrado por dominio**: incluso usuarios sin autenticar pueden ver checklists, pero **solo** aquellos marcados como públicos y que estén cerrados.

```yaml
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

---

## Hitos Técnicos

| Hito | Descripción |
|------|-------------|
| ✅ Primer modelo con `Base` | Uso de `field()`, `__model__`, `__service__`, `__selector_config__` |
| ✅ Primer `@exposed_action` | Decorador para exponer botones en la UI con control de grupos |
| ✅ Primera vista YAML completa | Lista + Formulario + Menú vinculados por `model_key` |
| ✅ Primer override de `create()` | Asignación automática de `owner_id` desde el contexto de sesión |
| ✅ Primera `bulk_action` | Operación masiva sobre múltiples registros seleccionados |
| ✅ Primer dominio ACL | Filtrado condicional para grupo público (`is_public + status`) |
| ✅ Soporte i18n | Directorio `i18n/` preparado para traducciones |
