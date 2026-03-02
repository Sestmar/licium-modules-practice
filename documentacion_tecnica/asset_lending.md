# 🏢 Asset Lending — Módulo Nivel 2

> **Módulo avanzado** de gestión de inventario y préstamos. Implementa lógica de estados cruzados entre modelos, UI dinámica autogenerada y **seguridad de doble capa** con control de acceso basado en dominio.

---

## Índice

- [Objetivo](#objetivo)
- [Modelos de Datos](#modelos-de-datos)
- [Lógica de Estados Cruzados (Services)](#lógica-de-estados-cruzados-services)
- [UI Dinámica](#ui-dinámica)
- [Seguridad Avanzada: Doble Capa](#seguridad-avanzada-doble-capa)
- [Resumen de Hitos Técnicos](#resumen-de-hitos-técnicos)

---

## Objetivo

Construir un sistema completo de **gestión de recursos e inventario** con las siguientes capacidades:

- Registro y catalogación de activos (equipos, dispositivos) con código único.
- Organización por **ubicaciones** (sedes, oficinas).
- Gestión del ciclo de vida de **préstamos**: creación, devolución y auditoría.
- Transiciones de estado automáticas entre modelos (`Loan` ↔ `Asset`).
- Control de acceso granular por grupo, incluyendo **restricciones por ubicación física**.

---

## Modelos de Datos

El módulo define tres entidades con relaciones de integridad referencial:

```
┌─────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  AssetLocation   │◄──────│     Asset         │◄──────│    AssetLoan      │
│─────────────────│  1:N  │──────────────────│  1:N  │──────────────────│
│ name             │       │ name              │       │ asset_id (FK)     │
│ code (unique)    │       │ asset_code (uniq) │       │ borrower_user_id  │
│ is_active        │       │ status            │       │ status            │
│                  │       │ location_id (FK)  │       │ checkout_at       │
│                  │       │ responsible_user  │       │ due_at            │
│                  │       │ notes             │       │ returned_at       │
└─────────────────┘       └──────────────────┘       └──────────────────┘
```

### `AssetLocation` — Ubicaciones

Sedes o puntos físicos donde se almacenan los recursos.

| Campo | Tipo | Propósito |
|-------|------|-----------|
| `name` | `String(180)` | Nombre de la ubicación (ej. "Oficina Madrid") |
| `code` | `String(50)`, unique | Código identificador corto (ej. `MAD-01`) |
| `is_active` | `Boolean` | Permite desactivar ubicaciones sin eliminarlas |

### `Asset` — Recursos / Activos

Elementos físicos que pueden prestarse (portátiles, cámaras, etc.).

| Campo | Tipo | Propósito |
|-------|------|-----------|
| `name` | `String(180)` | Nombre descriptivo del recurso |
| `asset_code` | `String(50)`, unique | Código de inventario único |
| `status` | `String(20)` | Estado actual: `available` · `on_loan` · `maintenance` |
| `location_id` | `FK → AssetLocation` | Ubicación física asignada |
| `responsible_user_id` | `FK → core_user` | Usuario responsable del recurso |

### `AssetLoan` — Préstamos

Registro de cada operación de préstamo y devolución.

| Campo | Tipo | Propósito |
|-------|------|-----------|
| `asset_id` | `FK → Asset` | Recurso prestado |
| `borrower_user_id` | `FK → core_user` | Usuario que recibe el préstamo |
| `status` | `String(20)` | `open` → `returned` |
| `checkout_at` | `DateTime` | Fecha/hora de salida |
| `due_at` | `DateTime` | Fecha límite de devolución |
| `returned_at` | `DateTime` | Fecha real de devolución (auto, `editable=False`) |
| `checkout_note` / `return_note` | `Text` | Notas de salida y devolución |

---

## Lógica de Estados Cruzados (Services)

El hito técnico más relevante del módulo es la **coordinación transaccional entre dos modelos** dentro de una misma acción expuesta.

### `AssetLoanService.return_asset()`

Cuando un préstamo se devuelve, la acción no solo actualiza el registro del préstamo: **recupera el modelo `Asset` asociado y restaura su estado a `available`**, todo dentro de la misma transacción de base de datos.

```python
class AssetLoanService(BaseService):
    from ..models import AssetLoan
    from ..models import Asset  # ← Importación cruzada: necesitamos otro modelo

    @exposed_action("write", groups=["asset_lending_group_manager", "core_group_superadmin"])
    def return_asset(self, id: int, note: str | None = None) -> dict:
        loan = self.repo.session.get(self.AssetLoan, int(id))
        if loan is None:
            raise HTTPException(404, "Loan not found")

        if loan.status != "open":
            raise HTTPException(400, "Este préstamo ya no está abierto.")

        # 1️⃣ Actualizar el préstamo
        loan.status = "returned"
        loan.returned_at = dt.datetime.now(dt.timezone.utc)
        if note:
            loan.return_note = note

        # 2️⃣ Actualizar el recurso asociado (estado cruzado)
        asset = self.repo.session.get(self.Asset, loan.asset_id)
        if asset:
            asset.status = "available"
            self.repo.session.add(asset)

        self.repo.session.add(loan)
        self.repo.session.commit()     # ← Una sola transacción atómica
        self.repo.session.refresh(loan)
        return serialize(loan)
```

**¿Por qué es importante?** La consistencia de datos se garantiza a nivel de transacción: si la actualización del `Asset` falla, el `Loan` tampoco se actualiza, evitando estados inconsistentes (un préstamo "devuelto" con un recurso que sigue "en préstamo").

### `AssetService` — Ciclo de Mantenimiento

El servicio de recursos expone acciones adicionales para la gestión del ciclo de vida:

| Acción | Grupos | Efecto |
|--------|--------|--------|
| `mark_maintenance()` | Manager, Técnico, Superadmin | `status → "maintenance"` + nota opcional |
| `release_maintenance()` | Manager, Técnico, Superadmin | `status → "available"` |

Nótese que el grupo **Técnico** (`asset_lending_group_tech`) tiene acceso a las acciones de mantenimiento, pero **no** a la devolución de préstamos — una separación de responsabilidades deliberada.

---

## UI Dinámica

### Diálogos autogenerados a partir del tipado Python

Una de las características más potentes del framework Licium es la **generación automática de ventanas de diálogo** ("prompts") basándose en la firma del método Python.

Cuando el `@exposed_action` recibe parámetros opcionales tipados, el frontend **autogenera un formulario modal** para que el usuario los rellene antes de ejecutar la acción:

```python
@exposed_action("write", groups=[...])
def return_asset(self, id: int, note: str | None = None) -> dict:
    #                              ^^^^^^^^^^^^^^^^^^^^^^^^
    #   El frontend detecta este parámetro y genera un campo de texto
    #   en un diálogo emergente antes de ejecutar la acción.
```

```python
@exposed_action("write", groups=[...])
def close(self, id: int, close_note: str | None = None, make_public: bool = False) -> dict:
    #                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #   Genera un diálogo con DOS campos: un texto y un checkbox.
```

No se necesita ninguna configuración adicional en el YAML: **el tipo Python es la interfaz**.

### `row_actions` — Botones contextuales por fila

En la vista de lista, cada fila puede tener botones de acción que llaman directamente a los métodos del servicio:

```yaml
row_actions:
  - key: return_item
    type: service
    label: "Devolver"
    icon: mdi-keyboard-return
    method: return_asset                 # ← Llama a AssetLoanService.return_asset()
    model_key: asset_lending.loan
    groups: [asset_lending_group_manager, core_group_superadmin]
```

El frontend renderiza el botón "Devolver" en cada fila de la lista de préstamos. Al hacer clic, si el método tiene parámetros opcionales (como `note`), aparece automáticamente un diálogo pidiendo esos datos.

### Ciclo completo: del botón al backend

```
 Clic "Devolver"       Diálogo auto        POST /api/...          Service
      (UI)         ──▶  note: str?    ──▶  return_asset()   ──▶  Loan.status = "returned"
                        [Aceptar]          id + note               Asset.status = "available"
```

---

## Seguridad Avanzada: Doble Capa

El reto técnico principal del Nivel 2 es implementar un **modelo de seguridad de dos capas** que actúe tanto a nivel de servicio como a nivel de datos.

### Capa 1: Autorización en el `@exposed_action`

El decorador controla **quién puede ejecutar una acción**. Solo los grupos listados tienen acceso al endpoint:

```python
@exposed_action("write", groups=[
    "asset_lending_group_manager",
    "asset_lending_group_tech",     # ← El técnico puede ejecutar acciones de mantenimiento
    "core_group_superadmin"
])
def mark_maintenance(self, id: int, note: str | None = None) -> dict:
    ...
```

Esta capa funciona como un **guardia de ruta**: si el usuario no pertenece a ninguno de los grupos listados, la petición se rechaza con un `403 Forbidden` antes de llegar al cuerpo del método.

### Capa 2: Restricción por dominio en las reglas ACL

Incluso si un usuario tiene permiso de escritura, una regla ACL con `domain` filtra **a qué registros concretos** puede acceder ese permiso:

```yaml
# El técnico puede LEER todos los recursos
- model: core.aclrule
  ext_id: asset_lending_acl_tech_asset_read
  fields:
    group_id.ext_id: asset_lending_group_tech
    model_key: "asset_lending.asset"
    perm_read: true

# Pero solo puede ESCRIBIR en recursos de la Ubicación 1
- model: core.aclrule
  ext_id: asset_lending_acl_tech_asset_write
  fields:
    group_id.ext_id: asset_lending_group_tech
    model_key: "asset_lending.asset"
    perm_write: true
    domain:
      - { field: "location_id", operator: "=", value: 1 }
```

### Resultado práctico

| Acción del Técnico | ¿Permitido? | Razón |
|--------------------|:-----------:|-------|
| Ver lista de todos los recursos | ✅ | `perm_read: true` sin dominio |
| Editar recurso en Ubicación 1 | ✅ | `perm_write` + dominio `location_id = 1` |
| Editar recurso en Ubicación 2 | ❌ | El dominio filtra: `location_id ≠ 1` |
| Devolver un préstamo | ❌ | `return_asset` no incluye `asset_lending_group_tech` |

### Diagrama de la doble capa

```
     Petición del Técnico: "Editar Asset #42"
                     │
        ┌────────────▼────────────┐
        │   CAPA 1: @exposed_action  │
        │   ¿Grupo autorizado?       │
        │   → tech ∈ groups? ✅      │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   CAPA 2: ACL + Domain     │
        │   ¿Permiso sobre ESTE      │
        │    registro específico?     │
        │   → Asset #42.location_id  │
        │     = 1? ✅ / ❌            │
        └────────────┬────────────┘
                     │
                ✅ Ejecutar  /  ❌ 403 Forbidden
```

**¿Por qué es importante?** El `@exposed_action` protege "qué puede hacer" un usuario. El dominio ACL protege "sobre qué datos" puede hacerlo. Juntos, implementan el **principio de mínimo privilegio** a nivel de registro, impidiendo que un técnico de una sede modifique los recursos de otra.

---

## Grupos del Módulo

| Grupo | `ext_id` | Permisos |
|-------|----------|----------|
| **Lector** | `asset_lending_group_reader` | Lectura de todos los modelos |
| **Gestor** | `asset_lending_group_manager` | CRUD completo en todos los modelos + devolver préstamos |
| **Técnico** | `asset_lending_group_tech` | Lectura global + escritura restringida a Ubicación 1 + acciones de mantenimiento |

---

## Resumen de Hitos Técnicos

| Hito | Descripción |
|------|-------------|
| ✅ Tres modelos relacionados | Entidades `Location` → `Asset` → `Loan` con FK y relaciones ORM |
| ✅ Lógica de estados cruzados | `return_asset()` actualiza `Loan` y `Asset` en una sola transacción |
| ✅ UI dinámica desde tipado | Diálogos autogenerados a partir de `str | None`, `bool`, etc. |
| ✅ `row_actions` en YAML | Botones contextuales por fila vinculados a métodos del servicio |
| ✅ Tres grupos de seguridad | Lector, Gestor y Técnico con responsabilidades separadas |
| ✅ ACL con dominio | Regla `domain: location_id = 1` que restringe escritura por ubicación |
| ✅ Seguridad de doble capa | `@exposed_action` (quién) + ACL domain (sobre qué datos) |
| ✅ Validación de estado | `HTTPException(400)` si el préstamo ya no está abierto |
| ✅ Separación de responsabilidades | El técnico puede mantener pero no devolver préstamos |
