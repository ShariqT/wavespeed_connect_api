"""Top-level package for wavespeed_connect_api."""

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]

__author__ = """Shariq Torres"""
__email__ = "shariq.torres@gmail.com"
__version__ = "0.0.1"

from .src.wavespeed_connect_api.nodes import NODE_CLASS_MAPPINGS
from .src.wavespeed_connect_api.nodes import NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"
