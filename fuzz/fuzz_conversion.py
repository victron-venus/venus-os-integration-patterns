"""Mutate the production value converter without importing host bindings."""
import json
import math
from pathlib import Path
import sys

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patterns/mqtt-to-dbus/src"))
with atheris.instrument_imports():
    from value_conversion import convert_value

BOUNDS = {"int32": (-(2**31), 2**31 - 1), "uint32": (0, 2**32 - 1), "uint16": (0, 65535)}


@atheris.instrument_func
def test_one_input(data):
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError, RecursionError):
        value = data.decode("utf-8", errors="replace")
    for kind in ("double", "int32", "uint32", "uint16", "boolean", "string"):
        try:
            result = convert_value(value, kind)
        except (ValueError, TypeError, OverflowError):
            continue
        if kind in BOUNDS:
            low, high = BOUNDS[kind]
            assert type(result) is int and low <= result <= high
        elif kind == "double":
            assert isinstance(result, float) and math.isfinite(result)
        elif kind == "boolean":
            assert type(result) is bool
        else:
            assert isinstance(result, str)
        assert convert_value(result, kind) == result


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()
