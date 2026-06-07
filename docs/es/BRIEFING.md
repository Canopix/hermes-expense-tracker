# Hermes Expense Tracker — Briefing

## Qué es

Sistema de **gastos compartidos del hogar** sobre **Hermes Agent**. Cada miembro puede tener su propio perfil Hermes (bot Telegram, CLI, etc.) y todos comparten **una sola SQLite** de gastos.

Los perfiles **solo conversan**. Toda la lógica de negocio vive en un **MCP server Python**. Los gastos **nunca** van a `state.db` ni `memories/` de Hermes.

**No hay deudas/balances** — solo `paid_by`, `allocations` (100%), y `person_summary` con `paid_total` vs `attributed_total`.

---

## Arquitectura

```
Perfil miembro A (Telegram/CLI)
Perfil miembro B (Telegram/CLI)
        ↓  tools: mcp_expense_tracker_*
Expense Tracker MCP (FastMCP, stdio, Python)
        ↓
~/expenses/data/expenses.db (SQLite compartida)
```

### Restricción de dominio

1. **SOUL.md** — rechaza temas fuera de gastos
2. **platform_toolsets: [mcp-expense-tracker]** — sin terminal, web, browser, etc.
3. **Skill expense-tracker** — workflow y ejemplos

Memoria Hermes deshabilitada: `memory.memory_enabled: false`

---

## Rutas (macOS)

| Qué | Ruta |
|-----|------|
| Repo producto | `~/hermes-expense-tracker/` |
| MCP server | `~/hermes-expense-tracker/mcp/expense-tracker/` |
| DB compartida | `~/expenses/data/expenses.db` |
| Perfiles runtime | `~/.hermes/profiles/<slug>/` |
| Hermes global | `~/.hermes/` |

---

## Estructura del repo (publicable)

```
hermes-expense-tracker/
├── bootstrap.sh
├── add-member.sh             # DB person + Hermes profile + SOUL
├── shared/seed-categories-en.sql
├── shared/seed-categories-es.sql
├── mcp/expense-tracker/
└── profiles/
    └── expense-member/       # único template (placeholders {{MEMBER_NAME}}, {{MEMBER_SLUG}})
```

**No hay perfiles con nombres reales en el repo.** `add-member.sh` materializa cada miembro en `~/.hermes/profiles/`.

---

## Seed

| Install (`bootstrap.sh`) | Tests |
|--------------------------|-------|
| Schema + **solo categorías** | Fixture con alice/bob + hogar + categorías |

Personas y proyectos se crean en instalación (`add-member.sh`) o por conversación (`create_project`, `create_person`).

Proyectos tienen **membresía por persona** (`project_members`). Cada perfil MCP recibe `EXPENSE_MEMBER_SLUG`. Personal = solo owner; compartido = owner invita con `members` o `add_project_member`. Solo el owner administra.

---

## MCP — 38 tools

Prefijo: `mcp_expense_tracker_<tool>`

CRUD de personas, proyectos (con `add_project_member`, `remove_project_member`, `list_project_members`), categorías y gastos (incluye `delete_*` con reglas de seguridad). Visibilidad de proyectos filtrada por `EXPENSE_MEMBER_SLUG`.

Reportes con filtros (`category`, `project`, `paid_by`, `allocated_to`, `currency`) y desgloses:
- `monthly_summary` → by_category, by_project, by_person
- `yearly_summary` → by_month, by_category, by_project
- `category_summary` → by_month, by_project
- `person_summary` → by_category, by_project (paid vs attributed)

`list_expenses` / `search_expenses`: paginación (`limit`, `offset`, `has_more`).

Comparación: `compare_months`, `compare_periods`. Top gastos: `top_expenses`. Export: `export_expenses` / `export_expenses_file`. Reportes: `generate_report` (markdown). Gráficos PNG: `render_chart` (matplotlib).

Presupuestos mensuales por categoría: `set_category_budget`, `budget_status` (alertas al superar umbral).

`add_expense`: allocations por slug; si no hay → 100% al pagador.

---

## Flujo de instalación

```bash
git clone https://github.com/Canopix/hermes-expense-tracker.git ~/hermes-expense-tracker
./bootstrap.sh
./add-member.sh alice Alice
./add-member.sh bob Bob
# .env + gateway por cada slug
```

---

## Comandos útiles

```bash
./bootstrap.sh
./add-member.sh <slug> <nombre>
hermes -p <slug> mcp test expense-tracker
<slug> gateway start
cd mcp/expense-tracker && .venv/bin/python -m unittest discover -s tests -v
```
