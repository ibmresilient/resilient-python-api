
from pkg_resources import resource_string

__version__ = resource_string(__name__, "version.txt").strip()
