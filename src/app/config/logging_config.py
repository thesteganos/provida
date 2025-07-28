import logging
from logging.handlers import RotatingFileHandler
from app.config.settings import settings
from pathlib import Path

def setup_logging():
    """
    Configura o sistema de logging da aplicação com base nas configurações do config.yaml.
    """
    log_settings = settings.logging

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_settings.level.upper()))

    # Clear existing handlers to prevent duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console output
    if log_settings.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File output for application logs
    if log_settings.file_output.enabled:
        log_dir = Path(log_settings.file_output.path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_settings.file_output.path,
            maxBytes=log_settings.file_output.max_bytes,
            backupCount=log_settings.file_output.backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Specific file output for system_log.txt (autonomous decisions)
    if log_settings.system_log.enabled:
        system_log_dir = Path(log_settings.system_log.path).parent
        system_log_dir.mkdir(parents=True, exist_ok=True)
        system_log_handler = RotatingFileHandler(
            log_settings.system_log.path,
            maxBytes=log_settings.file_output.max_bytes, # Reusing maxBytes/backupCount from general file_output
            backupCount=log_settings.file_output.backup_count
        )
        system_log_handler.setFormatter(formatter)
        system_log_handler.setLevel(getattr(logging, log_settings.system_log.level.upper()))
        # Create a specific logger for system_log to avoid duplicate messages in root_logger
        system_logger = logging.getLogger('system_log')
        system_logger.setLevel(getattr(logging, log_settings.system_log.level.upper()))
        system_logger.addHandler(system_log_handler)
        system_logger.propagate = False # Prevent messages from going to root_logger

    logging.info("Logging system configured.")
