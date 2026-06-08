"""Install wizard UI strings (en / es)."""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "title": "Hermes Expense Tracker",
        "subtitle": "Guided install · household expenses",
        "prereq_title": "Prerequisites",
        "prereq_intro": "Checking Python and Hermes Agent on your machine…",
        "prereq_check_python": "Python 3.11+",
        "prereq_check_hermes": "Hermes Agent (chat + Telegram)",
        "db_title": "Shared database",
        "db_intro": (
            "All household members read and write the **same** SQLite file.\n\n"
            "Default: [cyan]{default}[/cyan]\n"
            "Press Enter to keep the default, or type another path (file or folder)."
        ),
        "db_prompt": "Database path",
        "db_invalid": "Use a .db file path or a folder (we append expenses.db)",
        "db_saved": "Database path",
        "db_existing_note": "[dim]Existing database found at this path — your data will be kept.[/dim]",
        "bootstrap_title": "Expense server setup",
        "bootstrap_first_body": (
            "Setting up the expense server (Python tools Hermes calls) and creating:\n"
            "  [cyan]{path}[/cyan]\n\n"
            "Default categories will use your chosen language."
        ),
        "bootstrap_existing_db": (
            "Using existing expense database:\n"
            "  [cyan]{path}[/cyan]\n\n"
            "Your past expenses are kept. Next we'll only create Hermes profiles.\n\n"
            "[dim]To update the server after git pull, run ./update.sh — not here.[/dim]"
        ),
        "bootstrap_venv_only": "Expense server (Python) is missing — reinstalling it. Your database is not touched.",
        "bootstrap_running": "Installing Python packages and creating the shared database…",
        "bootstrap_running_venv": "Reinstalling expense server (Python packages)…",
        "members_title": "Household members",
        "members_intro": (
            "Each person who will **log expenses on their own Telegram** gets:\n"
            "  • a Hermes profile (e.g. [cyan]expense-alice[/cyan])\n"
            "  • their own bot — Alice and Bob each chat in **their** Telegram\n\n"
            "Everyone reads and writes the **same shared database**.\n"
            "If Alice logs groceries, Bob sees it when he asks his bot.\n\n"
            "[dim]Later you can add people who only appear in expenses (kids, relatives) "
            "without a bot.[/dim]"
        ),
        "members_count": "Members with their own Telegram bot",
        "display_name": "Display name (e.g. Alice, Bob)",
        "display_name_empty": "Display name cannot be empty",
        "slug": "Short id for commands (slug)",
        "slug_hint": "[dim]Used as alias: alice chat · profile name: expense-alice[/dim]",
        "slug_empty": "Slug cannot be empty",
        "slug_invalid": "Use lowercase letters, numbers, and hyphens only",
        "slug_no_prefix": "Do not use expense- prefix (e.g. alice, not expense-alice)",
        "extra_persons": "Add someone who only appears in expenses (no Telegram bot)?",
        "extra_name": "Name (empty = done)",
        "default_projects": "Create starter projects (home, vacation, health)?",
        "projects_title": "Projects",
        "done_title": "Install complete — next steps (each member)",
        "done_intro": "Install created profiles. Hermes still needs your model API key and Telegram bots.",
        "done_db": "Shared database",
        "done_step_model": "1. Model + API key",
        "done_step_mcp": "2. Verify expense tools",
        "done_step_telegram": "3. Telegram bot (BotFather token)",
        "done_step_pairing": "4. Pair Telegram",
        "done_pairing_help": "[dim]Message your bot → Hermes shows a code → hermes -p expense-<slug> pairing approve telegram CODE[/dim]",
        "done_step_chat": "5. First expense",
        "profiles": "Hermes profiles",
        "shortcut": "shortcut",
        "member_fail": "Failed",
        "project_created": "project",
        "project_exists": "project already exists",
        "project_synced": "members in project",
        "person_created": "Person without bot",
        "person_exists": "already exists",
        "need_one_member": "At least 1 member",
        "hermes_missing": "Install Hermes first: https://hermes-agent.nousresearch.com",
    },
    "es": {
        "title": "Hermes Expense Tracker",
        "subtitle": "Instalación guiada · gastos del hogar",
        "prereq_title": "Prerequisitos",
        "prereq_intro": "Verificando Python y Hermes Agent en tu máquina…",
        "prereq_check_python": "Python 3.11+",
        "prereq_check_hermes": "Hermes Agent (chat + Telegram)",
        "db_title": "Base compartida",
        "db_intro": (
            "Todos los miembros del hogar usan el **mismo** archivo SQLite.\n\n"
            "Default: [cyan]{default}[/cyan]\n"
            "Enter para default, o escribí otra ruta (archivo o carpeta)."
        ),
        "db_prompt": "Ruta de la base",
        "db_invalid": "Usá un archivo .db o una carpeta (agregamos expenses.db)",
        "db_saved": "Ruta de la base",
        "db_existing_note": "[dim]Ya existe una base en esa ruta — se conservan tus datos.[/dim]",
        "bootstrap_title": "Preparar el servidor de gastos",
        "bootstrap_first_body": (
            "Preparamos el servidor de gastos (herramientas Python que Hermes llama) y creamos:\n"
            "  [cyan]{path}[/cyan]\n\n"
            "Las categorías default usarán el idioma elegido."
        ),
        "bootstrap_existing_db": (
            "Usando base de gastos existente:\n"
            "  [cyan]{path}[/cyan]\n\n"
            "Tus gastos anteriores se mantienen. Ahora solo creamos perfiles Hermes.\n\n"
            "[dim]Para actualizar el servidor después de git pull, usá ./update.sh — no acá.[/dim]"
        ),
        "bootstrap_venv_only": "Falta el servidor de gastos (Python) — lo reinstalamos. La base no se toca.",
        "bootstrap_running": "Instalando paquetes Python y creando la base compartida…",
        "bootstrap_running_venv": "Reinstalando servidor de gastos (paquetes Python)…",
        "members_title": "Miembros del hogar",
        "members_intro": (
            "Cada persona que **registre gastos en su Telegram** recibe:\n"
            "  • un perfil Hermes (ej. [cyan]expense-alice[/cyan])\n"
            "  • su propio bot — Alice y Bob chatean cada uno en **su** Telegram\n\n"
            "Todos leen y escriben la **misma base compartida**.\n"
            "Si Alice anota el supermercado, Bob lo ve cuando le pregunta a su bot.\n\n"
            "[dim]Después podés sumar personas que solo figuren en gastos (chicos, familiares) "
            "sin bot.[/dim]"
        ),
        "members_count": "Miembros con bot de Telegram propio",
        "display_name": "Nombre para mostrar (ej. Alice, Bob)",
        "display_name_empty": "El nombre no puede estar vacío",
        "slug": "Id corto para comandos (slug)",
        "slug_hint": "[dim]Alias: alice chat · perfil Hermes: expense-alice[/dim]",
        "slug_empty": "El slug no puede estar vacío",
        "slug_invalid": "Usá solo letras minúsculas, números y guiones",
        "slug_no_prefix": "No uses prefijo expense- (ej. alice, no expense-alice)",
        "extra_persons": "¿Sumar alguien que solo figure en gastos (sin bot de Telegram)?",
        "extra_name": "Nombre (vacío = fin)",
        "default_projects": "¿Crear proyectos iniciales (hogar, vacaciones, salud)?",
        "projects_title": "Proyectos",
        "done_title": "Instalación lista — próximos pasos (por miembro)",
        "done_intro": "Los perfiles ya están creados. Falta configurar API key del modelo y bots de Telegram en Hermes.",
        "done_db": "Base compartida",
        "done_step_model": "1. Modelo + API key",
        "done_step_mcp": "2. Verificar herramientas de gastos",
        "done_step_telegram": "3. Bot Telegram (token de BotFather)",
        "done_step_pairing": "4. Emparejar Telegram",
        "done_pairing_help": "[dim]Escribile al bot → Hermes muestra un código → hermes -p expense-<slug> pairing approve telegram CODIGO[/dim]",
        "done_step_chat": "5. Primer gasto",
        "profiles": "Perfiles Hermes",
        "shortcut": "atajo",
        "member_fail": "Falló",
        "project_created": "proyecto",
        "project_exists": "proyecto ya existe",
        "project_synced": "miembros en proyecto",
        "person_created": "Persona sin bot",
        "person_exists": "Ya existe",
        "need_one_member": "Al menos 1 miembro",
        "hermes_missing": "Instalá Hermes primero: https://hermes-agent.nousresearch.com",
    },
}


def msg(locale: str, key: str) -> str:
    return MESSAGES.get(locale, MESSAGES["en"]).get(key, MESSAGES["en"].get(key, key))
