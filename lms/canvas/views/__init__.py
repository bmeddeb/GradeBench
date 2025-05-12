"""
Canvas views package
"""

from .courses import *
from .students import *
from .assignments import *
from .groups import *
from .sync import *
from .setup import *

# Backward compatibility with existing imports
from ..views import get_integration_for_user