import logging
import sys

DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

def get_logger(name: str, level: int = DEFAULT_LOG_LEVEL, fmt: str = DEFAULT_LOG_FORMAT) -> logging.Logger:
    """
    Initializes and returns a logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Example usage:
# from alpaca_simulator.common.logger import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message.")
