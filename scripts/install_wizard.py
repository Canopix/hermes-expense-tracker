#!/usr/bin/env python3
"""Quiet, panel-based installer wizard (Rich TUI)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
MCP_DIR = ROOT / "mcp" / "expense-tracker"
VENV_PY = MCP_DIR / ".venv" / "bin" / "python"
DB_PATH = Path.home() / "expenses" / "data" / "expenses.db"
LOCALE_FILE = Path.home() / "expenses" / "locale"
HERMES_MIN = "0.14.0"

sys.path.insert(0, str(ROOT / "scripts"))
from wizard_i18n import msg  # noqa: E402

console = Console()


def slugify(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    while slug.startswith("expense-"):
        slug = slug[len("expense-") :]
    return slug or "member"


def validate_slug(slug: str, locale: str) -> str | None:
    if not slug:
        return msg(locale, "slug_empty")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", slug):
        return msg(locale, "slug_invalid")
    if slug.startswith("expense-"):
        return msg(locale, "slug_no_prefix")
    return None


def save_household_locale(locale: str) -> None:
    LOCALE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCALE_FILE.write_text(f"{locale}\n", encoding="utf-8")


def ask_locale() -> str:
    console.print(
        Panel(
            "[bold]Household language / Idioma del hogar[/bold]\n"
            "  [cyan]1[/cyan]  English\n"
            "  [cyan]2[/cyan]  Español",
            title="Language / Idioma",
            border_style="blue",
        )
    )
    while True:
        choice = IntPrompt.ask("Choice / Opción", default=2)
        if choice == 1:
            return "en"
        if choice == 2:
            return "es"
        fail("1 or 2 / 1 o 2")


def run(cmd: list[str], *, quiet: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=ROOT, env=merged, text=True, capture_output=quiet, check=False)


def ok(message: str) -> None:
    console.print(f"  [green]✓[/green] {message}")


def warn(message: str) -> None:
    console.print(f"  [yellow]·[/yellow] {message}")


def fail(message: str) -> None:
    console.print(f"  [red]✗[/red] {message}")


def check_prerequisites(locale: str) -> bool:
    table = Table.grid(padding=(0, 2))
    table.add_column()
    table.add_column(style="dim")
    failed = False
    not_found = "not found" if locale == "en" else "no encontrado"
    profile_fail = "profile list failed" if locale == "en" else "profile list falló"

    py = shutil.which("python3")
    if not py:
        table.add_row("[red]✗[/red] python3", not_found)
        failed = True
    else:
        ver = subprocess.run([py, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"], capture_output=True, text=True)
        table.add_row("[green]✓[/green] python3", ver.stdout.strip() or "?")

    hermes = shutil.which("hermes")
    if not hermes:
        table.add_row("[red]✗[/red] hermes", not_found)
        failed = True
    else:
        ver_out = subprocess.run([hermes, "--version"], capture_output=True, text=True)
        match = re.search(r"(\d+\.\d+\.\d+)", ver_out.stdout + ver_out.stderr)
        version = match.group(1) if match else "?"
        list_ok = subprocess.run([hermes, "profile", "list"], capture_output=True).returncode == 0
        if not list_ok:
            table.add_row("[red]✗[/red] hermes", profile_fail)
            failed = True
        elif version != "?" and version < HERMES_MIN:
            table.add_row("[red]✗[/red] hermes", f"{version} < {HERMES_MIN}")
            failed = True
        else:
            table.add_row("[green]✓[/green] hermes", version)

    console.print(Panel(table, title=msg(locale, "prereq_title"), border_style="cyan"))
    return not failed


def bootstrap(locale: str) -> bool:
    console.print(
        Panel(f"[dim]{msg(locale, 'bootstrap_running')}[/dim]", title=msg(locale, "bootstrap_title"), border_style="cyan")
    )
    result = run(["bash", str(ROOT / "bootstrap.sh")], env={"QUIET": "1", "EXPENSE_LOCALE": locale})
    if result.returncode != 0:
        fail(msg(locale, "member_fail"))
        return False
    ok(f"{msg(locale, 'db_path')} {DB_PATH}")
    ok(msg(locale, "mcp_venv"))
    return True


def add_member(slug: str, display_name: str, locale: str) -> bool:
    result = run(
        ["bash", str(ROOT / "add-member.sh"), slug, display_name],
        env={"INSTALL_QUIET": "1", "SKIP_PREREQ": "1", "EXPENSE_LOCALE": locale},
    )
    if result.returncode != 0:
        fail(f"{msg(locale, 'member_fail')}: {display_name} ({slug})")
        if result.stderr:
            console.print(result.stderr, style="red dim")
        return False
    ok(
        f"{display_name} → {msg(locale, 'profiles')} [cyan]expense-{slug}[/cyan], "
        f"{msg(locale, 'shortcut')} [cyan]{slug}[/cyan]"
    )
    return True


def create_person_only(name: str, slug: str, locale: str) -> None:
    code = f"""
from expense_tracker import repositories as repo
from expense_tracker.db import init_db
init_db(seed=False)
try:
    repo.create_person({name!r}, slug={slug!r})
    print('created')
except repo.ValidationError as e:
    print('exists' if 'already exists' in str(e) else 'error')
"""
    result = run([str(VENV_PY), "-c", code], env={"PYTHONPATH": str(MCP_DIR), "EXPENSE_DB_PATH": str(DB_PATH)})
    if result.returncode == 0 and "created" in (result.stdout or ""):
        ok(f"{msg(locale, 'person_created')}: {name}")
    elif result.returncode == 0:
        warn(f"{msg(locale, 'person_exists')}: {slug}")


def seed_projects(member_slugs: list[str], locale: str) -> None:
    owner = member_slugs[0] if member_slugs else None
    members_json = repr(member_slugs[1:] if len(member_slugs) > 1 else [])
    if locale == "en":
        projects = [
            ("Home", "hogar", "Household expenses"),
            ("Vacation", "vacaciones", "Trips and getaways"),
            ("Health", "salud", "Health expenses"),
        ]
    else:
        projects = [
            ("Hogar", "hogar", "Gastos del hogar"),
            ("Vacaciones", "vacaciones", "Viajes y escapadas"),
            ("Salud", "salud", "Gastos de salud"),
        ]
    projects_repr = repr(projects)
    code = f"""
from expense_tracker import repositories as repo
from expense_tracker.db import init_db
init_db(seed=False)
owner = {owner!r}
extra_members = {members_json}
for name, slug, desc in {projects_repr}:
    try:
        repo.create_project(name, slug=slug, description=desc, owner=owner, members=extra_members)
        print('created:' + slug)
    except Exception as exc:
        if 'already exists' in str(exc):
            print('exists:' + slug)
        else:
            raise
    repo.sync_project_members_all_persons(slug)
    print('synced:' + slug)
"""
    result = run([str(VENV_PY), "-c", code], env={"PYTHONPATH": str(MCP_DIR), "EXPENSE_DB_PATH": str(DB_PATH)})
    for line in (result.stdout or "").splitlines():
        if line.startswith("created:"):
            ok(f"{msg(locale, 'project_created')} {line.split(':', 1)[1]}")
        elif line.startswith("exists:"):
            warn(f"{line.split(':', 1)[1]} {msg(locale, 'project_exists')}")
        elif line.startswith("synced:"):
            ok(f"{msg(locale, 'project_synced')} {line.split(':', 1)[1]}")


def show_summary(slugs: list[str], locale: str) -> None:
    primary = slugs[0] if slugs else "member"
    profile = f"expense-{primary}"
    profile_rows = "\n".join(
        f"  [cyan]expense-{s}[/cyan]  [dim]{msg(locale, 'shortcut')}:[/dim] {s}" for s in slugs
    )
    lines = [
        f"[bold]{msg(locale, 'profiles')}[/bold]",
        profile_rows,
        "",
        f"[bold]{msg(locale, 'mcp_test')}[/bold]   hermes -p {profile} mcp test expense-tracker",
        f"[bold]{msg(locale, 'onboarding')}[/bold] {primary} chat  [dim](= hermes -p {profile} chat)[/dim]",
        f"[bold]{msg(locale, 'model')}[/bold]     hermes -p {profile} setup",
        f"[bold]{msg(locale, 'telegram')}[/bold]   {primary} gateway setup · gateway start",
    ]
    console.print()
    console.print(
        Panel("\n".join(lines), title=f"[green]{msg(locale, 'done_title')}[/green]", border_style="green", padding=(1, 2))
    )


def main() -> int:
    locale = ask_locale()
    save_household_locale(locale)

    console.print(
        Panel(
            f"[bold]{msg(locale, 'title')}[/bold]\n[dim]{msg(locale, 'subtitle')}[/dim]",
            border_style="blue",
            padding=(1, 2),
        )
    )

    if not check_prerequisites(locale):
        return 1

    console.print()
    if not VENV_PY.exists():
        if not bootstrap(locale):
            return 1
    elif Confirm.ask(msg(locale, "bootstrap_prompt"), default=False):
        if not bootstrap(locale):
            return 1

    console.print()
    member_count = IntPrompt.ask(msg(locale, "members_count"), default=2)
    if member_count < 1:
        fail(msg(locale, "need_one_member"))
        return 1

    slugs: list[str] = []
    console.print(Panel(f"{member_count} profile(s)" if locale == "en" else f"{member_count} perfil(es)", title=msg(locale, "members_title"), border_style="cyan"))
    for i in range(1, member_count + 1):
        console.print(f"\n[bold]#{i}[/bold]")
        while True:
            display_name = Prompt.ask(f"  {msg(locale, 'display_name')}").strip()
            if display_name:
                break
            fail(msg(locale, "display_name_empty"))
        while True:
            slug = slugify(Prompt.ask(f"  {msg(locale, 'slug')}", default=slugify(display_name)))
            err = validate_slug(slug, locale)
            if err:
                fail(err)
                continue
            break
        if not add_member(slug, display_name, locale):
            return 1
        slugs.append(slug)

    if Confirm.ask(f"\n{msg(locale, 'extra_persons')}", default=False):
        while True:
            name = Prompt.ask(f"  {msg(locale, 'extra_name')}", default="")
            if not name.strip():
                break
            create_person_only(name.strip(), Prompt.ask("  Slug", default=slugify(name)), locale)

    if Confirm.ask(msg(locale, "default_projects"), default=True):
        console.print(Panel("", title=msg(locale, "projects_title"), border_style="cyan"))
        seed_projects(slugs, locale)

    show_summary(slugs, locale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
