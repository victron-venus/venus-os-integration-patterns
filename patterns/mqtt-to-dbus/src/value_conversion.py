"""Pure MQTT value conversion, shared by the bridge and offline fuzz tests."""

import math
from typing import Any


def convert_value(value: Any, dbus_type: str):
    """Return a representable value, raising for invalid numeric input."""
    integer_bounds = {
        "int32": (-(2**31), 2**31 - 1),
        "uint32": (0, 2**32 - 1),
        "uint16": (0, 2**16 - 1),
    }
    if dbus_type in integer_bounds:
        number = int(value)
        lower, upper = integer_bounds[dbus_type]
        if not lower <= number <= upper:
            raise ValueError(f"{dbus_type} out of range")
        return number
    if dbus_type == "boolean":
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if dbus_type == "string":
        return str(value)
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite double")
    return number
