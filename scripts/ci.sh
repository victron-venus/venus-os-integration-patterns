#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/validate-source.py
(
  cd patterns/mqtt-to-dbus
  PYTHONPATH=. python3 -m pytest tests/ -q
)

python3 -m unittest discover -s tests -p test_value_conversion.py
