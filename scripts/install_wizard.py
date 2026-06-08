#!/usr/bin/env python3
"""Guided installer wizard (Rich TUI — same stack as Hermes: rich + prompt_toolkit)."""

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
sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(ROOT / "scripts"))
from expense_tracker.paths import (  # noqa: E402
    db_path_override_file,
    default_db_path,
    expense_tracker_dir,
    is_legacy_db_path,
    locale_file,
)
from expense_cli.add_member import run_add_member  # noqa: E402
from expense_cli.bootstrap import run_bootstrap  # noqa: E402
from expense_cli.paths_util import write_env_paths  # noqa: E402
from expense_cli.runtime import find_system_python, venv_python  # noqa: E402
from wizard_i18n import msg  # noqa: E402
from wizard_banner import print_install_banner  # noqa: E402

DEFAULT_DB_PATH = default_db_path()
LOCALE_FILE = locale_file()
DB_PATH_FILE = db_path_override_file()
HERMES_MIN = "0.14.0"

console = Console()


def get_venv_python() -> Path:
    return venv_python()


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
    expense_tracker_dir().mkdir(parents=True, exist_ok=True)
    LOCALE_FILE.write_text(f"{locale}\n", encoding="utf-8")


def display_path(path: Path) -> str:
    resolved = path.expanduser().resolve()
    home = Path.home()
    try:
        rel = resolved.relative_to(home)
        return f"~/{rel}"
    except ValueError:
        return str(resolved)


def normalize_db_path(raw: str) -> Path:
    text = raw.strip()
    if not text:
        return DEFAULT_DB_PATH.expanduser().resolve()
    path = Path(os.path.expanduser(text))
    if text.endswith("/") or (path.exists() and path.is_dir()):
        path = path / "expenses.db"
    elif path.suffix != ".db":
        raise ValueError("expected .db file or directory")
    return path.resolve()


def load_stored_db_path() -> Path | None:
    if DB_PATH_FILE.exists():
        stored = DB_PATH_FILE.read_text(encoding="utf-8").strip()
        if stored:
            path = normalize_db_path(stored)
            if not is_legacy_db_path(path):
                return path
    return None


def save_household_db_path(path: Path) -> None:
    expense_tracker_dir().mkdir(parents=True, exist_ok=True)
    DB_PATH_FILE.write_text(f"{path}\n", encoding="utf-8")


def sync_env_paths(db_path: Path) -> None:
    write_env_paths(db_path)


def ask_db_path(locale: str) -> Path:
    stored = load_stored_db_path()
    default = stored or DEFAULT_DB_PATH
    panel_body = msg(locale, "db_intro").format(default=display_path(DEFAULT_DB_PATH))
    console.print(Panel(panel_body, title=msg(locale, "db_title"), border_style="cyan"))
    if default.exists():
        console.print(msg(locale, "db_existing_note"))

    while True:
        answer = Prompt.ask(f"  {msg(locale, 'db_prompt')}", default=display_path(default)).strip()
        try:
            path = normalize_db_path(answer)
        except ValueError:
            fail(msg(locale, "db_invalid"))
            continue
        break

    save_household_db_path(path)
    ok(f"{msg(locale, 'db_saved')}: {display_path(path)}")
    sync_env_paths(path)
    return path


def run_env(db_path: Path, locale: str) -> dict[str, str]:
    merged = os.environ.copy()
    merged.update(
        {
            "EXPENSE_DB_PATH": str(db_path),
            "EXPENSE_LOCALE": locale,
        }
    )
    return merged


def ask_locale() -> str:
    console.print(
        Panel(
            "[bold]Household language / Idioma del hogar[/bold]\n"
            "[dim]Bot replies, reports, and default category names[/dim]\n\n"
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
    console.print(f"[dim]{msg(locale, 'prereq_intro')}[/dim]")
    table = Table.grid(padding=(0, 2))
    table.add_column()
    table.add_column(style="dim")
    failed = False
    not_found = "not found" if locale == "en" else "no encontrado"
    profile_fail = "profile list failed" if locale == "en" else "profile list falló"

    with console.status(f"[cyan]•[/cyan] {msg(locale, 'prereq_check_python')}", spinner="dots"):
        py = find_system_python()
        if not py:
            table.add_row("[red]✗[/red] python", not_found)
            failed = True
        else:
            ver = subprocess.run(
                [str(py), "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
                capture_output=True,
                text=True,
            )
            detail = ver.stdout.strip() or "?"
            if subprocess.run(
                [str(py), "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"],
                capture_output=True,
            ).returncode != 0:
                detail = f"{detail} (< 3.11)"
            label = "python3" if shutil.which("python3") else "python"
            table.add_row(f"[green]✓[/green] {label}", detail)

    with console.status(f"[cyan]•[/cyan] {msg(locale, 'prereq_check_hermes')}", spinner="dots"):
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
    if failed:
        console.print(f"[red]{msg(locale, 'hermes_missing')}[/red]")
    return not failed


def bootstrap(db_path: Path, locale: str, *, venv_only: bool = False) -> bool:
    running = msg(locale, "bootstrap_running_venv" if venv_only else "bootstrap_running")
    console.print(Panel(running, title=msg(locale, "bootstrap_title"), border_style="cyan"))
    with console.status(running, spinner="dots"):
        for key, value in run_env(db_path, locale).items():
            os.environ[key] = value
        code = run_bootstrap(
            quiet=True,
            bootstrap_db=not venv_only,
            locale=locale,
            db_path=db_path,
        )
    if code != 0:
        fail(msg(locale, "member_fail"))
        return False
    ok(display_path(db_path))
    ok("expense-tracker MCP (Python venv)")
    return True


def add_member(db_path: Path, slug: str, display_name: str, locale: str) -> bool:
    with console.status(f"[cyan]•[/cyan] expense-{slug}", spinner="dots"):
        for key, value in run_env(db_path, locale).items():
            os.environ[key] = value
        os.environ["INSTALL_QUIET"] = "1"
        os.environ["SKIP_PREREQ"] = "1"
        code = run_add_member(slug, display_name, quiet=True, skip_prereq=True)
    if code != 0:
        fail(f"{msg(locale, 'member_fail')}: {display_name} ({slug})")
        return False
    ok(
        f"{display_name} → {msg(locale, 'profiles')} [cyan]expense-{slug}[/cyan], "
        f"{msg(locale, 'shortcut')} [cyan]{slug}[/cyan]"
    )
    return True


def create_person_only(db_path: Path, name: str, slug: str, locale: str) -> None:
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
    result = run(
        [str(get_venv_python()), "-c", code],
        env={"PYTHONPATH": str(MCP_DIR), "EXPENSE_DB_PATH": str(db_path)},
    )
    if result.returncode == 0 and "created" in (result.stdout or ""):
        ok(f"{msg(locale, 'person_created')}: {name}")
    elif result.returncode == 0:
        warn(f"{msg(locale, 'person_exists')}: {slug}")


def seed_projects(db_path: Path, member_slugs: list[str], locale: str) -> None:
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
    result = run(
        [str(get_venv_python()), "-c", code],
        env={"PYTHONPATH": str(MCP_DIR), "EXPENSE_DB_PATH": str(db_path)},
    )
    for line in (result.stdout or "").splitlines():
        if line.startswith("created:"):
            ok(f"{msg(locale, 'project_created')} {line.split(':', 1)[1]}")
        elif line.startswith("exists:"):
            warn(f"{line.split(':', 1)[1]} {msg(locale, 'project_exists')}")
        elif line.startswith("synced:"):
            ok(f"{msg(locale, 'project_synced')} {line.split(':', 1)[1]}")


def show_summary(db_path: Path, slugs: list[str], locale: str) -> None:
    primary = slugs[0] if slugs else "member"
    profile = f"expense-{primary}"
    profile_rows = "\n".join(
        f"  [cyan]expense-{s}[/cyan]  [dim]{msg(locale, 'shortcut')}:[/dim] {s}" for s in slugs
    )
    lines = [
        msg(locale, "done_intro"),
        "",
        f"[bold]{msg(locale, 'done_db')}[/bold]  {display_path(db_path)}",
        "",
        f"[bold]{msg(locale, 'profiles')}[/bold]",
        profile_rows,
        "",
        f"[bold]{msg(locale, 'done_step_model')}[/bold]",
        f"   hermes -p {profile} setup",
        "",
        f"[bold]{msg(locale, 'done_step_mcp')}[/bold]",
        f"   hermes -p {profile} mcp test expense-tracker",
        "",
        f"[bold]{msg(locale, 'done_step_telegram')}[/bold]",
        (
            f"   hermes -p {profile} gateway setup; hermes -p {profile} gateway start"
            if sys.platform == "win32"
            else f"   hermes -p {profile} gateway setup && hermes -p {profile} gateway start"
        ),
        "",
        f"[bold]{msg(locale, 'done_step_pairing')}[/bold]",
        f"   hermes -p {profile} pairing approve telegram <CODE>",
        msg(locale, "done_pairing_help"),
        "",
        f"[bold]{msg(locale, 'done_step_chat')}[/bold]",
        f"   hermes -p {profile} chat",
        '   [dim]"Log $50 at the pharmacy, I paid" / "Registrá $5000 en farmacia, pagué yo"[/dim]',
    ]
    console.print()
    console.print(
        Panel("\n".join(lines), title=f"[green]{msg(locale, 'done_title')}[/green]", border_style="green", padding=(1, 2))
    )


def main() -> int:
    print_install_banner(console)
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
    db_path = ask_db_path(locale)

    console.print()
    if not db_path.exists():
        console.print(
            Panel(
                msg(locale, "bootstrap_first_body").format(path=display_path(db_path)),
                title=msg(locale, "bootstrap_title"),
                border_style="cyan",
            )
        )
        if not bootstrap(db_path, locale):
            return 1
    elif not get_venv_python().exists():
        console.print(Panel(msg(locale, "bootstrap_venv_only"), title=msg(locale, "bootstrap_title"), border_style="cyan"))
        if not bootstrap(db_path, locale, venv_only=True):
            return 1
    else:
        sync_env_paths(db_path)
        console.print(
            Panel(
                msg(locale, "bootstrap_existing_db").format(path=display_path(db_path)),
                title=msg(locale, "bootstrap_title"),
                border_style="green",
            )
        )

    console.print()
    console.print(
        Panel(
            msg(locale, "members_intro"),
            title=msg(locale, "members_title"),
            border_style="cyan",
        )
    )
    member_count = IntPrompt.ask(f"  {msg(locale, 'members_count')}", default=2)
    if member_count < 1:
        fail(msg(locale, "need_one_member"))
        return 1

    slugs: list[str] = []
    console.print()
    for i in range(1, member_count + 1):
        console.print(f"\n[bold]#{i}[/bold]")
        while True:
            display_name = Prompt.ask(f"  {msg(locale, 'display_name')}").strip()
            if display_name:
                break
            fail(msg(locale, "display_name_empty"))
        console.print(f"  {msg(locale, 'slug_hint')}")
        while True:
            slug = slugify(Prompt.ask(f"  {msg(locale, 'slug')}", default=slugify(display_name)))
            err = validate_slug(slug, locale)
            if err:
                fail(err)
                continue
            break
        if not add_member(db_path, slug, display_name, locale):
            return 1
        slugs.append(slug)

    if Confirm.ask(f"\n{msg(locale, 'extra_persons')}", default=False):
        while True:
            name = Prompt.ask(f"  {msg(locale, 'extra_name')}", default="")
            if not name.strip():
                break
            create_person_only(db_path, name.strip(), Prompt.ask("  Slug", default=slugify(name)), locale)

    if Confirm.ask(msg(locale, "default_projects"), default=True):
        console.print(Panel("", title=msg(locale, "projects_title"), border_style="cyan"))
        seed_projects(db_path, slugs, locale)

    show_summary(db_path, slugs, locale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
