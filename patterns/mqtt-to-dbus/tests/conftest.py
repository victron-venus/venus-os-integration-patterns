"""Explicit host-binding stubs for offline unit tests.

These stubs are inert stand-ins so the pattern can be imported on hosts without
Venus D-Bus bindings. They are not native D-Bus or VRM validation.

Rules:
- Install only when the root package is not importable (find_spec / already loaded).
- Never replace a preexisting sys.modules entry or an available installed module.
- Restore every sys.modules change when the pytest session ends.
"""

from __future__ import annotations

import importlib.util
import sys
import types

_SAVED: dict[str, object | None] = {}
_INSTALLED: list[str] = []


def _importable(name: str) -> bool:
    if name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _dbus_stub_modules() -> dict[str, types.ModuleType]:
    dbus = types.ModuleType("dbus")

    class _Double(float):
        pass

    class _Int32(int):
        pass

    class _UInt32(int):
        pass

    class _UInt16(int):
        pass

    class _String(str):
        pass

    class _Boolean(int):
        pass

    class _Object:
        def __init__(self, *args, **kwargs):
            pass

    class _SystemBus:
        def __init__(self, *args, **kwargs):
            pass

        def request_name(self, *args, **kwargs):
            return None

    dbus.SystemBus = _SystemBus
    dbus.Double = _Double
    dbus.Int32 = _Int32
    dbus.UInt32 = _UInt32
    dbus.UInt16 = _UInt16
    dbus.String = _String
    dbus.Boolean = _Boolean
    dbus.service = types.ModuleType("dbus.service")
    dbus.service.Object = _Object
    dbus.service.method = lambda *args, **kwargs: lambda fn: fn
    dbus.service.signal = lambda *args, **kwargs: lambda fn: fn
    dbus.bus = types.ModuleType("dbus.bus")
    dbus.bus.NAME_FLAG_DO_NOT_QUEUE = 1
    dbus.exceptions = types.ModuleType("dbus.exceptions")

    class DBusException(Exception):
        def __init__(self, *args, name=None):
            super().__init__(*args)
            self.name = name

    dbus.exceptions.DBusException = DBusException
    mainloop = types.ModuleType("dbus.mainloop")
    glib = types.ModuleType("dbus.mainloop.glib")
    glib.DBusGMainLoop = lambda set_as_default=False: None
    return {
        "dbus": dbus,
        "dbus.service": dbus.service,
        "dbus.bus": dbus.bus,
        "dbus.exceptions": dbus.exceptions,
        "dbus.mainloop": mainloop,
        "dbus.mainloop.glib": glib,
    }


def _gi_stub_modules() -> dict[str, types.ModuleType]:
    gi = types.ModuleType("gi")
    repository = types.ModuleType("gi.repository")

    class GLib:
        class MainLoop:
            def run(self):
                return None

            def quit(self):
                return None

    repository.GLib = GLib
    gi.repository = repository
    return {"gi": gi, "gi.repository": repository}


def _install_tree(modules: dict[str, types.ModuleType]) -> None:
    for name, module in modules.items():
        if name in sys.modules:
            # Never overwrite an existing entry.
            continue
        _SAVED[name] = None
        sys.modules[name] = module
        _INSTALLED.append(name)


def pytest_configure(config) -> None:
    """Install missing host stubs before test collection imports the bridge."""
    del config  # unused; required pytest hook signature
    if not _importable("dbus"):
        _install_tree(_dbus_stub_modules())
    if not _importable("gi"):
        _install_tree(_gi_stub_modules())


def pytest_unconfigure(config) -> None:
    """Restore sys.modules entries introduced by this conftest."""
    del config
    for name in reversed(_INSTALLED):
        prior = _SAVED.get(name)
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
    _INSTALLED.clear()
    _SAVED.clear()
