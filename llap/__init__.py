import logging
from logging import NullHandler
from .constants import *

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())
