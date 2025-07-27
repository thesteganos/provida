import os
import re
import yaml
from pathlib import Path

def load_config():
    """
    Load reporting configurations from config.yaml.
    """
    config_path = Path(__file__).parent.parent.parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    def expand(value):
        if isinstance(value, str):
            pattern = re.compile(r"\$\{([^}]+)\}")

            def repl(match):
                var = match.group(1)
                return os.environ.get(var, match.group(0))

            return pattern.sub(repl, value)
        elif isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [expand(v) for v in value]
        return value

    return expand(config)

# Load the configuration globally for other modules to use
settings = load_config()

# Expose reporting-related configurations for easy access
reporting_enabled = settings['reporting']['enabled']
reporting_interval = settings['reporting']['interval']
reporting_formats = settings['reporting']['formats']
reporting_output_path = settings['reporting']['output_path']