# Install instructions (copy to another AI or person)

Use this text when asking someone (or an agent with terminal access) to install the product on a machine with Hermes.

---

## Goal

Install **Hermes Expense Tracker**: shared household expenses. Each member can have their own Telegram bot; everyone shares one SQLite database.

## Requirements

- macOS or Linux with `python3` 3.11+
- [Hermes Agent](https://hermes-agent.nousresearch.com) >= 0.14.0 on PATH (`hermes --version`)
- Model and Telegram are configured **after** install in each Hermes profile (`config.yaml` / `hermes setup` / `gateway setup`) — not part of `install.sh`

`install.sh` automatically checks python3, that `hermes` exists, responds, meets the minimum version, and that `hermes profile list` works.

## Steps (in terminal)

```bash
cd ~
git clone https://github.com/Canopix/hermes-expense-tracker.git hermes-expense-tracker
cd hermes-expense-tracker
chmod +x install.sh bootstrap.sh add-member.sh
./install.sh
```

The `install.sh` wizard asks interactively:

1. **Household language** — `English` or `Español` (bot copy + report labels)
2. Whether to run bootstrap (MCP + DB) — say yes
3. **How many members** will have their own bot
4. For each: **display name** and **slug** (e.g. `maria` / `Maria`)
5. Whether there are people **without a bot** (expenses only)
6. Whether to create default projects (home, vacation, health)

## After install (per member)

At the path printed by `add-member.sh` (typically `~/.hermes/profiles/expense-<slug>/`):

| Step | Command |
|------|---------|
| Model | `hermes -p <slug> setup` |
| Gateway | `<slug> gateway setup && <slug> gateway start` |
| Pairing | `hermes -p <slug> pairing approve telegram <CODE>` |
| Verify MCP | `hermes -p <slug> mcp test expense-tracker` → 38 tools |

## Onboarding in Hermes (conversational)

When MCP is working:

```bash
<primary-slug> chat
```

Say: *"Let's set up"* or *"First time"*.

The agent (`onboarding` skill) guides: extra projects, budgets, first expense. It **does not** create Hermes profiles — that is only via `install.sh` / `add-member.sh`.

## Verification

```bash
cd ~/hermes-expense-tracker/mcp/expense-tracker
.venv/bin/python -m unittest discover -s tests -v
```

## Do not

- Do not commit `config.yaml` with secrets or runtime profile tokens
- Do not put real people's data in the repo (only in `~/expenses/data/expenses.db`)
- Do not compute debts between people (out of scope)
