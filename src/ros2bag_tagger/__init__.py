from importlib.metadata import version as _v

__all__ = ["__version__"]

try:
    __version__ = _v(__name__)
except Exception:
    __version__ = "0.0.0"
