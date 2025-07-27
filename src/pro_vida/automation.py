from .config import load_config

# Load the configuration globally for other modules to use
settings = load_config()

# Expose automation-related configurations for easy access
automation_enabled = settings['automation']['enabled']
automation_interval = settings['automation']['interval']
automation_tasks = settings['automation']['tasks']