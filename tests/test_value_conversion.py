"""Offline conversion contract; no D-Bus, MQTT, GLib or network required."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patterns/mqtt-to-dbus/src"))
from value_conversion import convert_value


class ValueConversion(unittest.TestCase):
    def test_representable_values_and_numeric_bounds(self):
        for kind, low, high in (("int32", -(2**31), 2**31-1), ("uint32", 0, 2**32-1), ("uint16", 0, 65535)):
            for value in (low, high):
                self.assertEqual(convert_value(str(value), kind), value)
            for value in (low-1, high+1):
                with self.assertRaises(ValueError):
                    convert_value(value, kind)
        self.assertEqual(convert_value("25.5", "double"), 25.5)
        self.assertEqual(convert_value(100.7, "int32"), 100)
        self.assertTrue(convert_value("YES", "boolean"))
        self.assertFalse(convert_value("false", "boolean"))
        self.assertEqual(convert_value(123, "string"), "123")

    def test_nonfinite_values_are_not_valid_dbus_numbers(self):
        for value in ("nan", "inf", "-inf", "1e999", float("nan"), float("inf")):
            for kind in ("double", "int32", "uint32", "uint16"):
                with self.subTest(value=value, kind=kind), self.assertRaises((ValueError, OverflowError)):
                    convert_value(value, kind)
