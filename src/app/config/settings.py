import os
import yaml
from dotenv import load_dotenv

load_dotenv()

def load_config():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    for section, services in config["services"].items():
        for key, value in services.items():
            if isinstance(value, str) and value.startswith("${"):
                var_name = value[2:-1]
                default_value = None
                if ":-" in var_name:
                    var_name, default_value = var_name.split(":-", 1)
                config["services"][section][key] = os.getenv(var_name, default_value)

    return config

settings = load_config()
