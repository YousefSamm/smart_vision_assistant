"""Logging utilities for Smart Glass"""

import logging


def setup_logger(name=None, level=logging.INFO):
    """Setup and return a logger instance"""
    logger = logging.getLogger(name or __name__)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

