# Licium Modules — Colección de Módulos de Práctica

> Repositorio de módulos personalizados desarrollados para el framework **Licium**: un entorno Dockerizado basado en **Python/FastAPI** (backend), **PostgreSQL** (persistencia) y un frontend **Nuxt** que renderiza interfaces de usuario declaradas en **YAML**.

---

## 📚 Índice

- [Arquitectura de un Módulo](#-arquitectura-de-un-módulo)
- [Módulos Incluidos](#-módulos-incluidos)
- [Módulo 3 — Feedback & Moderación](#-módulo-3--feedback--moderación)
- [Puesta en Marcha](#-puesta-en-marcha)
- [Cómo Ejecutar los Tests del Sistema](#-cómo-ejecutar-los-tests-del-sistema)
- [Notas para Desarrolladores](#-notas-para-desarrolladores)
- [Estructura del Repositorio](#-estructura-del-repositorio)

---

## 🏗 Arquitectura de un Módulo

Cada módulo sigue una separación estricta en capas, lo que garantiza la mantenibilidad y la escalabilidad del código:

```
modules/mi_modulo/
├── __init__.py              # Registro del módulo (importa models y services)
├── __manifest__.yaml        # Metadatos, dependencias y orden de carga de datos
├── models/                  # 🗄️  Capa de Datos — Definición de tablas (SQLAlchemy)
│   ├── __init__.py
│   └── mi_modelo.py
├── services/                # ⚙️  Capa de Negocio — Lógica, validaciones y acciones
│   ├── __init__.py
│   └── mi_servicio.py
├── views/                   # 🖼️  Capa de Presentación — UI declarativa (YAML)
│   ├── views.yml            #     Definición de listas y formularios
│   └── menu.yml             #     Menú de navegación y acciones de ruta
└── data/                    # 🔐 Capa de Seguridad y Configuración
    ├── groups.yml            #     Grupos de permisos (Lector, Gestor, etc.)
    ├── acl_rules.yml         #     Reglas ACL con dominio condicional
    └── ui_modules.yml        #     Registro del módulo en el frontend
```

### Flujo de una petición

```
     HTTP Request
          │
          ▼
  ┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
  │  FastAPI Route │────▶│  Service Layer   │────▶│  Model (ORM)     │
  │  (auto-gen)    │     │  @exposed_action │     │  SQLAlchemy Base │
  └───────────────┘     └─────────────────┘     └──────────────────┘
          │                      │                        │
          │               ACL + Groups              PostgreSQL
          │              ◄──────────────►
          ▼
  ┌───────────────┐
  │  Frontend UI   │  ◄── views.yml + menu.yml (declarativo)
  │  (Nuxt, auto)  │
  └───────────────┘
```

El backend expone automáticamente endpoints REST a partir de los modelos registrados. Las vistas YAML se interpretan en el frontend para generar listas, formularios, menús y diálogos sin escribir una sola línea de JavaScript.

---

## Módulos Incluidos

| Módulo | Nivel | Descripción | Documentación |
|--------|:-----:|-------------|:-------------:|
| `practice_checklist` | 1 | Gestor de tareas y checklists con acciones de apertura/cierre | [📄 Ver docs](docs/practice_checklist.md) |
| `asset_lending` | 2 | Sistema de inventario, ubicaciones y préstamos con seguridad avanzada | [📄 Ver docs](docs/asset_lending.md) |
| `feedback_moderation` | 3 | Moderación de sugerencias y comentarios con seguridad dinámica y M2M | [📄 Ver docs](docs/feedback_moderation.md) |

---

## � Módulo 3 — Feedback & Moderación

### Resumen Funcional

Este módulo gestiona el **ciclo de vida de sugerencias y comentarios ciudadanos**, permitiendo la moderación activa por parte de administradores y la visualización selectiva para el público. Las sugerencias pasan por una máquina de estados (`pending → published / rejected / merged`) y solo el contenido aprobado y marcado como público es visible para usuarios no moderadores.

### Hitos Técnicos Alcanzados

| Hito | Descripción |
|------|-------------|
| ✅ **Relaciones Complejas** | Implementación de relaciones Many-to-Many entre `Suggestion` y `Tag` con tabla de asociación y `back_populates` |
| ✅ **Seguridad Dinámica** | Uso de Domain Rules en ACL para filtrar contenido sensible en tiempo real — solo se muestra lo `published` e `is_public` |
| ✅ **UI Reactiva** | Configuración de `row_actions` en vistas de lista para ejecutar acciones de servicio (`publish`, `reject`, `merge`) con un solo clic |
| ✅ **Calidad de Código** | Cobertura de tests unitarios para las transiciones de estado críticas (`pending → published / rejected`) |
| ✅ **Formularios Autogenerados** | Diálogos modales generados automáticamente a partir del tipado Python (`str \| None`, `bool`, `int`) |

### ⚠️ Lección Nivel 3: Tipado UUID en Foreign Keys

> Al relacionar tablas con `core_user` en Licium, las FK **deben ser de tipo `Uuid`**, no `Integer`. El campo `core_user.id` es UUID nativo de PostgreSQL.

| Configuración | Tipo FK | Resultado |
|:---|:---:|:---|
| ❌ Incorrecta | `Integer` | `DatatypeMismatch` — PostgreSQL rechaza la constraint |
| ✅ Correcta | `Uuid` | Constraint creada correctamente, persistencia funcional |

```python
# ❌ Provoca DatatypeMismatch
reviewed_by_id = field(Integer, ForeignKey("core_user.id"), ...)

# ✅ Correcto: core_user.id es UUID
reviewed_by_id = field(Uuid, ForeignKey("core_user.id"), ...)
```

---

## �🚀 Puesta en Marcha

### Requisitos previos

- **Docker** y **Docker Compose** instalados.
- Puerto `8000` (backend), `3000` (frontend) y `5432` (PostgreSQL) disponibles.

### 1. Clonar y levantar el entorno

```bash
git clone <https://github.com/Sestmar/licium-modules-practice>
cd modules_practice

# Levantar los 3 servicios en modo desarrollo
docker compose -f docker-compose.backend-dev.yml up -d
```

Docker Compose levantará automáticamente:

| Servicio | Contenedor | Puerto |
|----------|-----------|--------|
| PostgreSQL 17 | `licium-postgres-dev` | `5432` |
| Backend FastAPI | `licium-backend-dev` | `8000` |
| Frontend Nuxt | `licium-frontend-dev` | `3000` |

### 2. Instalación base de Licium

Una vez los contenedores estén **healthy**, abrir en el navegador:

```
http://localhost:8000/api/install
```

Esto ejecuta la instalación base del framework: crea las tablas del core, los grupos de administración y el usuario inicial.

### 3. Instalar los módulos

Desde la terminal del host, utilizar la **CLI** integrada de Licium:

```bash
# Instalar el módulo Practice Checklist
docker exec -it licium-backend-dev \
  python -m app.cli.module install modules/practice_checklist -y

# Instalar el módulo Asset Lending
docker exec -it licium-backend-dev \
  python -m app.cli.module install modules/asset_lending -y

# Instalar el módulo Feedback Moderation
docker exec -it licium-backend-dev \
  python -m app.cli.module install modules/feedback_moderation -y
```

### 4. Acceder al frontend

```
http://localhost:3000
```

Iniciar sesión con las credenciales de administrador creadas durante la instalación.

---

## 🧪 Cómo Ejecutar los Tests del Sistema

Los módulos incluyen tests unitarios que validan la lógica de negocio. Para ejecutarlos dentro del contenedor Docker:

```bash
# Tests del módulo Feedback Moderation
docker exec -it licium-backend-dev python -m pytest modules/feedback_moderation/tests/ -v
```

Salida esperada:

```
tests/test_suggestion_states.py::test_publish_suggestion_success             PASSED
tests/test_suggestion_states.py::test_publish_already_published_raises_error  PASSED
tests/test_suggestion_states.py::test_reject_suggestion                      PASSED
tests/test_suggestion_states.py::test_merge_suggestion_with_itself_raises_error  PASSED

========================= 4 passed =========================
```

> **Nota**: Los tests utilizan `unittest.mock.MagicMock` para simular la sesión de base de datos, por lo que no requieren una instancia de PostgreSQL activa.

---

## ⚠️ Notas para Desarrolladores

### Volúmenes y renombrado de carpetas

> **Si se renombra la carpeta raíz del proyecto** (ej. de `modules_practice` a `my_project`), Docker Compose creará un **nuevo volumen** de PostgreSQL con un nombre derivado del directorio. Los datos existentes quedarán huérfanos en el volumen anterior.
>
> **Solución**: eliminar los volúmenes antiguos antes de reconstruir.

```bash
docker compose -f docker-compose.backend-dev.yml down -v
docker compose -f docker-compose.backend-dev.yml up -d
# Repetir: /api/install + CLI de instalación de módulos
```

### Orden estricto de lectura en `__manifest__.yaml`

El archivo `__manifest__.yaml` define el orden exacto en que el framework carga los ficheros de datos. Este orden es **crítico**:

```yaml
data:
  - data/groups.yml       # 1️⃣ Primero: crear grupos de seguridad
  - data/acl_rules.yml    # 2️⃣ Segundo: reglas ACL (dependen de los grupos)
  - data/ui_modules.yml   # 3️⃣ Tercero: registrar el módulo en el frontend
  - views/views.yml       # 4️⃣ Cuarto: definir vistas (listas y formularios)
  - views/menu.yml        # 5️⃣ Quinto: menú y acciones (dependen de las vistas)
```

Si una vista referencia un `ext_id` de un grupo que aún no se ha creado, la instalación fallará. **Respetar siempre la cadena de dependencias**.

---

## 🗂 Estructura del Repositorio

```
modules_practice/
├── .env                                # Variables de entorno para Docker Compose
├── docker-compose.backend-dev.yml      # Orquestación de servicios (dev)
├── filestore/                          # Archivos subidos y logs del framework
├── modules/
│   ├── practice_checklist/             # 📋 Módulo Nivel 1
│   ├── asset_lending/                  # 🏢 Módulo Nivel 2
│   └── feedback_moderation/            # 💬 Módulo Nivel 3
├── docs/
│   ├── practice_checklist.md           # Documentación del Módulo 1
│   ├── asset_lending.md               # Documentación del Módulo 2
│   └── feedback_moderation.md         # Documentación del Módulo 3
└── README.md                           # ← Este archivo
```

---

## 📝 Licencia

Uso interno — Desarrollado durante las prácticas en [Libnamic](https://libnamic.com).
