"""Register a household member in DB + Hermes profile."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from .locale_util import resolve_expense_locale
from .paths_util import resolve_expense_db_path, write_env_paths
from .prereqs import require_prerequisites
from .runtime import (
    MCP_DIR,
    REPO_ROOT,
    TEMPLATE_DIR,
    env_path_value,
    hermes_profiles_dir,
    mcp_env,
    run_hermes,
    venv_python,
)
from .slug import normalize_member_slug, validate_member_slug


def log(message: str, *, quiet: bool) -> None:
    if not quiet:
        print(message)


def _upsert_env_var(env_file: Path, key: str, value: str) -> None:
    lines: list[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()
    lines = [line for line in lines if not line.startswith(f"{key}=")]
    lines.append(f"{key}={value}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _alias_exists(slug: str) -> bool:
    if shutil.which(slug):
        return True
    local_bin = Path.home() / ".local" / "bin" / slug
    return local_bin.exists()


def run_add_member(raw_slug: str, display_name: str, *, quiet: bool = False, skip_prereq: bool = False) -> int:
    if not skip_prereq and not require_prerequisites():
        return 1

    locale = resolve_expense_locale()
    if not locale:
        return 1

    locale_dir = REPO_ROOT / "locales" / locale
    if not (locale_dir / "SOUL.md").exists():
        print(f"Missing locale files: {locale_dir / 'SOUL.md'}", file=sys.stderr)
        return 1

    slug = normalize_member_slug(raw_slug)
    if not validate_member_slug(slug):
        return 1
    if raw_slug != slug:
        print(f"Nota: slug normalizado '{raw_slug}' → '{slug}'", file=sys.stderr)

    profile_name = f"expense-{slug}"
    db_path = resolve_expense_db_path()
    venv_py = venv_python()
    if not venv_py.exists():
        print("MCP venv not found. Run bootstrap first.", file=sys.stderr)
        return 1

    log(f"==> Registering person '{slug}' in shared database", quiet=quiet)
    code = f"""
from expense_tracker import repositories as repo
from expense_tracker.db import init_db

init_db(seed=False)
slug = {slug!r}
name = {display_name!r}
try:
    person = repo.create_person(name, slug=slug)
    print(f"created:{{person['slug']}}")
except repo.ValidationError as exc:
    if "already exists" in str(exc):
        print(f"exists:{{slug}}")
    else:
        raise
"""
    env = mcp_env(db_path)
    result = __import__("subprocess").run(
        [str(venv_py), "-c", code],
        env=env,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode
    log((result.stdout or "").strip(), quiet=quiet)

    log(f"==> Hermes profile {profile_name}", quiet=quiet)
    show = run_hermes(["profile", "show", profile_name], quiet=True)
    if show.returncode == 0:
        log(f"Profile {profile_name} already exists — skipping install", quiet=quiet)
    else:
        args = ["profile", "install", str(TEMPLATE_DIR), "--name", profile_name, "-y"]
        install = run_hermes(args, quiet=quiet)
        if install.returncode != 0:
            print(install.stderr or install.stdout, file=sys.stderr)
            return install.returncode

    if _alias_exists(slug):
        log(f"Alias '{slug}' already exists — skipping", quiet=quiet)
    elif run_hermes(["profile", "show", profile_name], quiet=True).returncode == 0:
        log(f"==> Creating alias '{slug}' → {profile_name}", quiet=quiet)
        alias = run_hermes(["profile", "alias", profile_name, "--name", slug], quiet=quiet)
        if alias.returncode != 0:
            print(alias.stderr or alias.stdout, file=sys.stderr)
            return alias.returncode

    profile_dir = hermes_profiles_dir() / profile_name
    if not profile_dir.is_dir():
        print(f"Profile directory missing: {profile_dir}", file=sys.stderr)
        return 1

    log(f"==> Personalizing SOUL for {display_name} (slug: {slug}, locale: {locale})", quiet=quiet)
    soul = (locale_dir / "SOUL.md").read_text(encoding="utf-8")
    soul = soul.replace("{{MEMBER_NAME}}", display_name).replace("{{MEMBER_SLUG}}", slug)
    (profile_dir / "SOUL.md").write_text(soul, encoding="utf-8")

    skills_src = locale_dir / "skills"
    if skills_src.is_dir():
        skills_dst = profile_dir / "skills"
        skills_dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skills_src, skills_dst, dirs_exist_ok=True)

    env_file = profile_dir / ".env"
    env_file.touch(exist_ok=True)

    _upsert_env_var(env_file, "EXPENSE_DB_PATH", env_path_value(db_path))
    _upsert_env_var(env_file, "EXPENSE_MCP_PYTHON", env_path_value(venv_python()))
    _upsert_env_var(env_file, "EXPENSE_MCP_SERVER_PATH", env_path_value(MCP_DIR / "server.py"))
    _upsert_env_var(env_file, "EXPENSE_MEMBER_SLUG", slug)
    _upsert_env_var(env_file, "EXPENSE_LOCALE", locale)

    write_env_paths(db_path)

    if not quiet:
        print(f"==> Profile ready: {profile_name} (atajo: {slug})")
        print(f"    Path: {profile_dir}")
        print(f"Next: hermes -p {profile_name} setup · hermes -p {profile_name} gateway setup · gateway start")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print("Usage: add_member.py <slug> <display_name>", file=sys.stderr)
        print("  Set EXPENSE_LOCALE=en|es or run install first.", file=sys.stderr)
        return 1
    quiet = os.environ.get("INSTALL_QUIET", "").strip() != ""
    skip = os.environ.get("SKIP_PREREQ", "").strip() != ""
    return run_add_member(args[0], args[1], quiet=quiet, skip_prereq=skip)


if __name__ == "__main__":
    sys.exit(main())
