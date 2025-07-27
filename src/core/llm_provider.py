import os
import re
import yaml
from pathlib import Path

def load_config():
    """
    Load model configurations from config.yaml.
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

# Expose model-related configurations for easy access
llm_enabled = settings['models']['llm']['enabled']
llm_api_key = settings['models']['llm']['api_key']
llm_endpoint = settings['models']['llm']['endpoint']
llm_timeout = settings['models']['llm']['timeout']

class LLM:
    def __init__(self, api_key, endpoint, timeout):
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    def generate_text(self, prompt):
        """
        Generate text using the LLM.
        """
        # Placeholder for actual LLM text generation logic
        return f"Generated text for prompt: {prompt}"

# Example usage
if __name__ == "__main__":
    llm = LLM(llm_api_key, llm_endpoint, llm_timeout)
    response = llm.generate_text("Hello, LLM!")
    print(response)