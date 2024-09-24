from importlib.metadata import version

from .goodman_focus import GoodmanFocus  # noqa: F401
from .goodman_focus import run_goodman_focus  # noqa: F401

__version__ = version('goodman_focus')
