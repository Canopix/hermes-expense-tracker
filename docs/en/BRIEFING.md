# Hermes Expense Tracker — Briefing

## What it is

**Shared household expense** system on **Hermes Agent**. Each member can have their own Hermes profile (Telegram bot, CLI, etc.) and everyone shares **one SQLite** expense database.

Profiles **only chat**. All business logic lives in a **Python MCP server**. Expenses **never** go to Hermes `state.db` or `memories/`.

**No debts/balances** — only `paid_by`, `allocations` (100%), and `person_summary` with `paid_total` vs `attributed_total`.

---

## Architecture

```
Member profile A (Telegram/CLI)
Member profile B (Telegram/CLI)
        ↓  tools: mcp_expense_tracker_*
Expense Tracker MCP (FastMCP, stdio, Python)
        ↓
~/expenses/data/expenses.db (shared SQLite)
```

### Domain restriction

1. **SOUL.md** — rejects off-topic requests
2. **platform_toolsets: [mcp-expense-tracker]** — no terminal, web, browser, etc.
3. **expense-tracker skill** — workflow and examples

Hermes memory disabled: `memory.memory_enabled: false`

---

## Paths (macOS)

| What | Path |
|------|------|
| Product repo | `~/hermes-expense-tracker/` |
| MCP server | `~/hermes-expense-tracker/mcp/expense-tracker/` |
| Shared DB | `~/expenses/data/expenses.db` |
| Runtime profiles | `~/.hermes/profiles/<slug>/` |
| Hermes global | `~/.hermes/` |
| Household locale | `~/expenses/locale` |

---

## Repo structure (publishable)

```
hermes-expense-tracker/
├── bootstrap.sh
├── add-member.sh             # DB person + Hermes profile + SOUL from locales/
├── locales/en|es/            # SOUL + skills per language
├── shared/seed-categories-en.sql
├── shared/seed-categories-es.sql
├── mcp/expense-tracker/
└── profiles/
    └── expense-member/       # Hermes shell template ({{MEMBER_NAME}}, {{MEMBER_SLUG}})
```

**No real names in the repo.** `add-member.sh` materializes each member in `~/.hermes/profiles/`.

---

## Seed

| Install (`bootstrap.sh`) | Tests |
|--------------------------|-------|
| Schema + **categories only** | Fixture with alice/bob + hogar + categories |

People and projects are created at install (`add-member.sh`) or by conversation (`create_project`, `create_person`).

Projects have **per-person membership** (`project_members`). Each MCP profile receives `EXPENSE_MEMBER_SLUG`. Personal = owner only; shared = owner invites via `members` or `add_project_member`. Only the owner administers.

---

## Internationalization

- Wizard asks language first; saves `~/.expenses/locale`
- `EXPENSE_LOCALE` (`en` \| `es`) in profile `.env` and MCP env
- Agent copy from `locales/${LOCALE}/`
- Report/chart strings via `expense_tracker/i18n.py`
- Code and MCP errors stay English

---

## MCP — 38 tools

Prefix: `mcp_expense_tracker_<tool>`

CRUD for persons, projects (with `add_project_member`, `remove_project_member`, `list_project_members`), categories, and expenses (including `delete_*` with safety rules). Project visibility filtered by `EXPENSE_MEMBER_SLUG`.

Reports with filters (`category`, `project`, `paid_by`, `allocated_to`, `currency`) and breakdowns:
- `monthly_summary` → by_category, by_project, by_person
- `yearly_summary` → by_month, by_category, by_project
- `category_summary` → by_month, by_project
- `person_summary` → by_category, by_project (paid vs attributed)

`list_expenses` / `search_expenses`: pagination (`limit`, `offset`, `has_more`).

Comparison: `compare_months`, `compare_periods`. Top expenses: `top_expenses`. Export: `export_expenses` / `export_expenses_file`. Reports: `generate_report` (markdown). PNG charts: `render_chart` (matplotlib).

Monthly category budgets: `set_category_budget`, `budget_status` (alerts when over threshold).

`add_expense`: allocations by slug; if none → 100% to payer.

---

## Install flow

```bash
git clone https://github.com/Canopix/hermes-expense-tracker.git ~/hermes-expense-tracker
./install.sh                  # asks language, then members
# or manual:
./bootstrap.sh
EXPENSE_LOCALE=en ./add-member.sh alice Alice
EXPENSE_LOCALE=en ./add-member.sh bob Bob
# .env + gateway per slug
```

---

## Useful commands

```bash
./bootstrap.sh
EXPENSE_LOCALE=en ./add-member.sh <slug> <name>
hermes -p <slug> mcp test expense-tracker
<slug> gateway start
cd mcp/expense-tracker && .venv/bin/python -m unittest discover -s tests -v
```
