import yaml
from pathlib import Path

def load_config():
    """
    Carrega as configurações do arquivo config.yaml na raiz do projeto.
    """
    config_path = Path(__file__).parent.parent.parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

# Carrega a configuração globalmente para que outros módulos possam importá-la
settings = load_config()