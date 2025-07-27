from .config import load_config

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
