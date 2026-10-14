#!/usr/bin/env bash
set -euo pipefail

if ! command -v pkg >/dev/null 2>&1 || [[ "${PREFIX:-}" != *"/com.termux/files/usr" ]]; then
  echo "This setup script is for Termux on Android. On other systems, follow the standard README quick start." >&2
  exit 1
fi

case "${1:-}" in
  ""|--with-dev) ;;
  *) echo "Usage: bash scripts/termux-setup.sh [--with-dev]" >&2; exit 2 ;;
esac

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

pkg update -y
pkg install -y git python rust clang make pkg-config

python -m venv .venv
install_target='.'
if [[ "${1:-}" == "--with-dev" ]]; then
  install_target='.[dev]'
fi
.venv/bin/python -m pip install -e "$install_target"

printf '
Setup complete. Activate the environment with:
  . .venv/bin/activate
'
printf 'Copy .env.example to .env, then start with:
  python -m app
'
