import logging
from logging.handlers import RotatingFileHandler
from app.config.settings import settings
from pathlib import Path

def setup_logging():
    """
    Configura o sistema de logging da aplicação Pró-Vida.

    As configurações de logging são carregadas do `config.yaml` e incluem:
    - Nível de logging global (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    - Saída para o console.
    - Saída para arquivo de log principal (`application.log`) com rotação.
    - Saída para um arquivo de log específico para decisões autônomas (`system_log.txt`).

    Erros na criação de diretórios ou arquivos de log são capturados e logados.
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
        try:
            log_dir = Path(log_settings.file_output.path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_settings.file_output.path,
                maxBytes=log_settings.file_output.max_bytes,
                backupCount=log_settings.file_output.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError as e:
            logging.error(f"Failed to create log directory or file for application logs: {e}")

    # Specific file output for system_log.txt (autonomous decisions)
    if log_settings.system_log.enabled:
        try:
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
        except OSError as e:
            logging.error(f"Failed to create log directory or file for system logs: {e}")

    logging.info("Logging system configured.")
