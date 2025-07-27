from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        self.api_key = os.getenv("API_KEY", "your_api_key_here")
        self.base_url = os.getenv("BASE_URL", "https://api.example.com")
        self.timeout = int(os.getenv("TIMEOUT", 30))  # in seconds
        self.entrez_api_key = os.getenv("ENTREZ_API_KEY", "your_entrez_api_key_here")

settings = Settings()