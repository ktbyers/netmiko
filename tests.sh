#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "Running ruff format check..."
uv run --frozen ruff format --check .

echo -e "\nRunning ruff linter..."
uv run --frozen ruff check .

echo -e "\nRunning mypy type checker..."
uv run --frozen mypy ./netmiko/

echo -e "\nRunning pytest..."
uv run --frozen pytest -v -s tests/test_import_netmiko.py
uv run --frozen pytest -v -s tests/unit/test_base_connection.py
uv run --frozen pytest -v -s tests/unit/test_fortinet.py
uv run --frozen pytest -v -s tests/unit/test_utilities.py
uv run --frozen pytest -v -s tests/unit/test_ssh_autodetect.py
uv run --frozen pytest -v -s tests/unit/test_connection.py
uv run --frozen pytest -v -s tests/unit/test_entry_points.py
uv run --frozen pytest -v -s tests/unit/test_session_log.py
