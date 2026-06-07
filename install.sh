#!/usr/bin/env bash
# Launcher — UI in scripts/install_wizard.py (Rich panels, quiet bootstrap)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="${ROOT}/mcp/expense-tracker/.venv/bin/python"
WIZARD="${ROOT}/scripts/install_wizard.py"

# Venv only — DB seed runs in the wizard after locale is chosen.
if [[ ! -x "${VENV_PY}" ]]; then
  QUIET=1 BOOTSTRAP_DB=0 "${ROOT}/bootstrap.sh"
fi

exec "${VENV_PY}" "${WIZARD}"
