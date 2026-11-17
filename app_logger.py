"""
app_logger: Custom logger for bostDepo
"""
import logging
from typing import Optional
import sys


def setup_logger(name: str, level: Optional[str] = 'DEBUG') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # create formatter for logger
    if level == 'DEBUG':
        formatter = logging.Formatter(
             '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "logger":"%(name)s", "message":"%(message)s"}',
             datefmt='%Y-%m-%d %H:%M:%S'
             )
    else:
        formatter = logging.Formatter('%(name)s - %(message)s')
    # create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger 

