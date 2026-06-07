# Hermes Expense Tracker

Expense tracker para tu hogar sobre [Hermes Agent](https://hermes-agent.nousresearch.com): cada miembro de la familia tiene su propio asistente conversacional (Telegram, CLI, etc.), todos comparten **una sola base de datos** de gastos, y toda la lógica vive en un MCP Python.

Repositorio: [github.com/Canopix/hermes-expense-tracker](https://github.com/Canopix/hermes-expense-tracker)

- Los perfiles **solo conversan**; no calculan ni persisten gastos por su cuenta.
- **No hay deudas** ni balances entre personas (`paid_by` ≠ `attributed`, sin settlements).
- Ideal para pareja, familia, roommates o cualquier grupo que comparta gastos del hogar.

Documentación en inglés: [README.md](../../README.md) · [docs/en/](../en/)

---

## Inicio rápido (con Hermes ya instalado)

```bash
git clone https://github.com/Canopix/hermes-expense-tracker.git ~/hermes-expense-tracker
cd ~/hermes-expense-tracker
chmod +x install.sh bootstrap.sh add-member.sh
./install.sh
```

Luego **por cada miembro** (reemplazá `alice` por tu slug):

- [ ] `hermes -p alice setup` — modelo + API key
- [ ] `alice gateway setup && alice gateway start` — bot Telegram
- [ ] `hermes -p alice pairing approve telegram <CODIGO>`
- [ ] `hermes -p alice mcp test expense-tracker` — **38 tools, ✓ Connected**
- [ ] `alice chat` — *"Registrá $5000 en farmacia, pagué yo"*

---

## Cómo funciona

**Camino de cada mensaje:**

1. **Miembro** — Telegram o `alice chat`
2. **Perfil Hermes** — `expense-<slug>` carga SOUL + skills desde `locales/`
3. **MCP server** — ejecuta la tool (`add_expense`, `generate_report`, …)
4. **Base de datos** — `~/expenses/data/expenses.db` (SQLite compartida)

| De | A | Cómo |
|----|---|------|
| Miembro | Perfil Hermes | chat / gateway |
| Perfil | MCP | stdio — `mcp_expense_tracker_*` |
| MCP | SQLite | `EXPENSE_DB_PATH` (igual en todos los perfiles) |

Cada perfil envía `EXPENSE_MEMBER_SLUG` (visibilidad de proyectos) y `EXPENSE_LOCALE` (idioma de reportes).

---

## Internacionalización (EN + ES)

Durante `./install.sh`, el wizard **siempre pregunta** el idioma del hogar primero (`English` o `Español`).

| Capa | Idioma |
|------|--------|
| Código, tests, errores MCP | Inglés (canónico) |
| `README.md`, `docs/en/` | Inglés |
| `docs/es/` | Español |
| SOUL + skills del agente | `locales/en/` o `locales/es/` |
| Reportes y gráficos | `EXPENSE_LOCALE` (`en` \| `es`) |
| Nombres de categorías default | Seed al bootstrap según locale (`shared/seed-categories-en.sql` / `-es.sql`) |
| Slugs de categorías | Iguales en todos los locales (`supermercado`, `transporte`, …) |

- El locale se guarda en `~/.expenses/locale` y en `.env` de cada perfil como `EXPENSE_LOCALE`.
- Instalación manual: `EXPENSE_LOCALE=es ./add-member.sh alice Alice`
- Installs viejos sin locale: `./update.sh` usa **español** por defecto.

---

## Prerequisitos

- [Hermes Agent](https://hermes-agent.nousresearch.com) instalado (`hermes --version`)
- Python 3.11+
- API key del modelo LLM que uses (OpenRouter, endpoint propio, etc.)
- Un bot de Telegram **por persona** que quiera chatear (vía [@BotFather](https://t.me/BotFather))

---

## Instalación rápida

### Opción A — Guiada (recomendada)

Wizard en terminal con paneles (Rich): prerequisitos, preguntas cortas, sin spam de `pip`. Verifica Python 3 + Hermes >= 0.14.0.

```bash
git clone https://github.com/Canopix/hermes-expense-tracker.git ~/hermes-expense-tracker
cd ~/hermes-expense-tracker
chmod +x install.sh bootstrap.sh add-member.sh
./install.sh
```

> Instrucciones para otra IA: [`PARA-INSTALAR.md`](PARA-INSTALAR.md) · English: [`docs/en/TO-INSTALL.md`](../en/TO-INSTALL.md)

### Opción B — Manual

```bash
./bootstrap.sh
EXPENSE_LOCALE=es ./add-member.sh alice Alice
EXPENSE_LOCALE=es ./add-member.sh bob Bob
```

`bootstrap.sh` crea el MCP, la DB (solo categorías) y `.env.paths`.  
`add-member.sh` registra la persona en DB + perfil Hermes + SOUL.

### Después del install — configurar Hermes (por perfil)

`add-member.sh` imprime la ruta del perfil (típicamente `~/.hermes/profiles/expense-<slug>/`). Los comandos usan el **alias** `<slug>` (`alice gateway`, `hermes -p alice`).

**Qué configura cada capa:**

| Qué | Dónde | Cómo |
|-----|--------|------|
| Rutas del MCP (`EXPENSE_*`) | Entorno del perfil | `add-member.sh` las agrega automáticamente (resuelven `${...}` en `config.yaml`) |
| Modelo / provider / API key | `config.yaml` del perfil | `hermes setup` o editar a mano |
| Telegram, gateway, pairing | `config.yaml` + gateway | `<slug> gateway setup` |
| SOUL, skills, toolsets | Perfil instalado | Copiados desde `locales/` en install |

Este producto **no** pide API keys ni tokens en `install.sh`. Eso es Hermes.

### Telegram y arranque

```bash
alice gateway setup
alice gateway start
hermes -p alice pairing approve telegram <CODIGO>
```

Verificar MCP:

```bash
hermes -p alice mcp test expense-tracker
# 38 tools, "✓ Connected"
```

Probar:

```bash
alice chat
# "Registrá $5000 en farmacia, pagué yo" / "¿Cuánto gastamos este mes?"
```

Repetir secrets + Telegram para cada miembro (`bob`, etc.).

### Checklist post-install (por miembro)

| Paso | Comando | Esperado |
|------|---------|----------|
| Modelo | `hermes -p <slug> setup` | Provider + API key |
| MCP | `hermes -p <slug> mcp test expense-tracker` | 38 tools, ✓ Connected |
| Gateway | `<slug> gateway setup && <slug> gateway start` | Gateway corriendo |
| Pairing | `hermes -p <slug> pairing approve telegram <CODIGO>` | Bot responde |
| Smoke test | `./scripts/smoke-test.sh expense-<slug>` | Gasto + consulta del mes |

### UX en Telegram (silencioso)

El template `expense-member` viene configurado para un chat limpio:

| Setting | Efecto |
|---------|--------|
| `display.tool_progress: off` | Sin mensajes `⚙️ mcp_expense_tracker_*` |
| `display.interim_assistant_messages: false` | Sin narración intermedia ("Te creo la categoría...") |
| `telegram.reactions: true` | 👀 mientras procesa, 👍 al terminar |
| SOUL + skill | Confirmación estructurada (`Listo ✅` + bullets 📅💰🏷️👤📊), sin narrar tools |

**Slug del miembro:** solo el nombre corto (`emanuel`, `johanna`). **No** uses `expense-johanna` — `add-member.sh` agrega el prefijo `expense-` al perfil Hermes.

Los installs nuevos heredan UX del template. `add-member.sh` siempre re-personaliza el SOUL (también después de `profile update`).

Las reacciones de Telegram (👀/👍) son fijas en Hermes; no se pueden cambiar a ⏳/✅ sin modificar Hermes Agent.

### Onboarding conversacional (dentro de Hermes)

Con el MCP ya conectado, el primer chat puede guiar proyectos, presupuestos y el primer gasto:

```bash
alice chat
# "Empecemos la configuración" / "Primera vez"
```

El skill `onboarding` hace preguntas de a una. **No** crea perfiles ni bots (eso es `install.sh`); sí usa MCP para proyectos, presupuestos y gastos.

### Qué podés pedirle al bot (ejemplos)

- *"Registrá $8000 en farmacia, pagué yo"*
- *"¿Cuánto gastamos en junio?"* / *"¿Junio vs mayo?"*
- *"Top 5 gastos del mes"*
- *"Gastos del proyecto hogar"*
- *"Creá proyecto Vacaciones 2027"*
- *"Seteá presupuesto de $50.000 en supermercado"*
- *"¿Qué presupuestos estoy por romper?"*
- *"Exportá junio en CSV"*

---

## Personas sin bot (solo aparecen en gastos)

Si alguien participa en gastos pero no chatea (ej. un hijo, un familiar):

- Desde cualquier perfil: *"Creá la persona Tía Rosa"*
- El agente usa `mcp_expense_tracker_create_person`
- Queda en la DB para allocations y reportes
- **No** requiere `./add-member.sh` ni bot Telegram

---

## Qué tocás vos vs qué no

| Acción | ¿Código? | Cómo |
|--------|----------|------|
| Instalar | No | `git clone` + `./bootstrap.sh` |
| Miembro con chat | No | `EXPENSE_LOCALE=es ./add-member.sh <slug> <nombre>` |
| Modelo / API key | No | `config.yaml` del perfil o `hermes setup` |
| Telegram | No | `gateway setup` + BotFather |
| Pairing | No | `hermes -p <slug> pairing approve telegram CODE` |
| Persona solo en gastos | No | Pedirle al bot "creá persona X" |
| Proyectos del hogar | No | Pedirle al bot "creá proyecto vacaciones" |
| Presupuestos por categoría | No | Pedirle al bot o usar `set_category_budget` |
| Actualizar todo | No | `./update.sh` (MCP + skills + SOUL + Telegram UX) |
| Perfil mal nombrado | No | `./scripts/repair-profile.sh johanna Johanna expense-expense-johanna` |
| Limpiar DB duplicados | No | `./scripts/cleanup-db.sh` |

**Nunca se pisa en updates:** `.env`, `memories/`, `sessions/`, `state.db`, `pairing/`.

---

## Dónde vive cada cosa

| Componente | Ubicación |
|------------|-----------|
| Repo (MCP + template) | `~/hermes-expense-tracker/` |
| Perfiles Hermes (runtime) | `~/.hermes/profiles/expense-<slug>/` (comandos: alias `<slug>`) |
| Base de datos compartida | `~/expenses/data/expenses.db` |
| Locale del hogar | `~/expenses/locale` |
| Config del perfil | `~/.hermes/profiles/expense-<slug>/config.yaml` |

---

## Estructura del repo

```
hermes-expense-tracker/
├── README.md                 # inglés (canónico)
├── locales/
│   ├── en/                   # SOUL + skills (inglés)
│   └── es/                   # SOUL + skills (español)
├── install.sh                # wizard guiado (recomendado)
├── bootstrap.sh              # MCP venv + DB (categorías default)
├── add-member.sh             # Persona en DB + perfil Hermes + SOUL localizado
├── docs/
│   ├── en/                   # BRIEFING, TO-INSTALL
│   └── es/                   # README, BRIEFING, PARA-INSTALAR
├── .env.EXAMPLE
├── shared/seed-categories-en.sql
├── shared/seed-categories-es.sql
├── mcp/expense-tracker/
│   ├── server.py             # 38 tools FastMCP
│   ├── manifest.yaml
│   └── expense_tracker/
│       └── i18n.py           # strings de reportes (en/es)
└── profiles/
    └── expense-member/       # shell Hermes (sin SOUL duplicado)
```

---

## MCP tools

38 tools. Prefijo en Hermes: `mcp_expense_tracker_<tool>`.

| Grupo | Tools |
|-------|-------|
| Personas | `create_person`, `update_person`, `list_persons`, `delete_person` |
| Proyectos | `create_project`, `update_project`, `list_projects`, `add_project_member`, `remove_project_member`, `list_project_members`, `delete_project` |
| Categorías | `create_category`, `update_category`, `list_categories`, `delete_category` |
| Gastos | `add_expense`, `update_expense`, `delete_expense`, `list_expenses`, `search_expenses` |
| Reportes | `monthly_summary`, `yearly_summary`, `project_summary`, `category_summary`, `person_summary` |
| Comparación / export | `compare_months`, `compare_periods`, `top_expenses`, `export_expenses`, `export_expenses_file` |
| Reportes / gráficos | `generate_report`, `render_chart` (PNG: categorías, proyectos, tendencia, top gastos) |
| Presupuestos | `set_category_budget`, `update_category_budget`, `delete_category_budget`, `list_category_budgets`, `budget_status` |
| Utilidad | `health_check` |

`list_expenses` y `search_expenses` devuelven paginación (`items`, `total_count`, `has_more`, `offset`). Los reportes aceptan filtros por categoría, proyecto, persona (`paid_by` / `allocated_to`) y moneda.

### Proyectos con membresía

Cada perfil Hermes envía `EXPENSE_MEMBER_SLUG` al MCP (en `.env` del perfil). Los proyectos tienen miembros explícitos:

- **Personal** — solo el owner (`create_project` sin `members`)
- **Compartido** — owner + invitados (`create_project(..., members=["johanna"])`)
- Solo el owner administra miembros, archiva o borra
- Gastos en proyectos ajenos no aparecen en listados ni reportes del caller

`./update.sh` corre migraciones y re-aplica `EXPENSE_MEMBER_SLUG` en perfiles existentes.

---

## Tests

```bash
cd mcp/expense-tracker
.venv/bin/python -m unittest discover -s tests -v
```

---

## Actualizar

```bash
cd ~/hermes-expense-tracker
git pull                    # si usás git
./update.sh                 # bootstrap + todos los expense-* perfiles
```

`update.sh` hace: MCP, migraciones DB (membresía de proyectos), `profile update`, re-personaliza SOUL vía `add-member.sh`, aplica Telegram UX + `EXPENSE_MEMBER_SLUG`, reinicia gateways.

Probar después:

```bash
./scripts/smoke-test.sh expense-alice
```

Perfil con nombre duplicado (`expense-expense-johanna`):

```bash
./scripts/repair-profile.sh johanna Johanna expense-expense-johanna
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| MCP no conecta | `hermes -p <slug> mcp test expense-tracker`; revisar `EXPENSE_MCP_*` en entorno del perfil |
| Gastos distintos por perfil | `EXPENSE_DB_PATH` debe ser **idéntica** en todos los perfiles |
| Telegram no responde | `<slug> gateway status`; token y `allow_from` |
| Pairing rechazado | `hermes -p <slug> pairing approve telegram CODE` (con `-p`) |
| Agente fuera de dominio | Verificar `platform_toolsets: [mcp-expense-tracker]` en `config.yaml` |
| Persona no existe al registrar gasto | `./add-member.sh` o `create_person` desde el bot |
| Perfil `expense-expense-*` | `./scripts/repair-profile.sh <slug> <nombre> <perfil-viejo>` |
| SOUL con `{{MEMBER_NAME}}` | `./add-member.sh <slug> <nombre>` o `./update.sh` |
| Reportes en idioma incorrecto | `EXPENSE_LOCALE=en` o `es` en `.env` del perfil, luego `./update.sh` |
