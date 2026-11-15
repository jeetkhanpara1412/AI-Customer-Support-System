import sys

from loguru import logger


def configure_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, serialize=True, enqueue=True, backtrace=False, diagnose=False)
