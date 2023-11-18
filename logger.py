import logging
from config import Config

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Further configuration...
    return logger

