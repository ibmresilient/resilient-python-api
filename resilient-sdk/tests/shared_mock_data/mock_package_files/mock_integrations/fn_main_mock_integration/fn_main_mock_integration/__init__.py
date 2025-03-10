try:
    from importlib.metadata import distribution, PackageNotFoundError
except ImportError:
    from importlib_metadata import distribution, PackageNotFoundError
try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    __version__ = None
