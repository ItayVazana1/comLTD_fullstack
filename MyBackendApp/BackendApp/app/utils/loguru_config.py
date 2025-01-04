from loguru import logger
import sys

def setup_loguru():
    # Clear default handlers to avoid duplicate logs
    logger.remove()

    # Add a custom handler for console logging
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",  # Adjust log level as needed
        colorize=True,
    )
    return logger

loguru_logger = setup_loguru()
