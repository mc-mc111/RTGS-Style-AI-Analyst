import logging
import sys
import os
from datetime import datetime
from rich.logging import RichHandler

def setup_logger():
    """
    Sets up a single, project-wide logger that uses RichHandler for
    beautiful console output and a FileHandler for detailed logs.
    """
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger('rtgs_ai_analyst')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )
    log_filename = f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    console_handler = RichHandler(
        show_path=False, log_time_format="[%X]", markup=True
    )
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def log_error_and_exit(logger_instance: logging.Logger, exc: Exception):
    """Logs the full exception and provides a clean exit for the user."""
    logger_instance.critical("A critical error occurred. Traceback:", exc_info=True)
    logger_instance.info(f"\n[bold red]ERROR:[/bold red] {exc}")
    logger_instance.info("The program has halted. Please check the latest `.log` file in the 'logs' directory for detailed information.")
    sys.exit(1)

# --- KEY CHANGE: Create the logger instance ONCE when this module is imported ---
logger = setup_logger()

