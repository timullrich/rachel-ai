"""Lazy exports for GTAF runtime integration helpers."""

from importlib import import_module

__all__ = ["GtafRuntimeClient", "GtafRuntimeConfig"]

_MODULE_BY_ATTR = {
    "GtafRuntimeClient": ".runtime_client",
    "GtafRuntimeConfig": ".runtime_client",
}


def __getattr__(name: str):
    if name not in _MODULE_BY_ATTR:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(_MODULE_BY_ATTR[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals().keys()) | set(__all__))
