import os
import requests

class BraveSearch:
    def __init__(self):
        self.api_key = os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY not found in environment variables.")
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

    def search(self, query: str, count: int = 10) -> dict:
        """Performs a search using the Brave Search API.

        Args:
            query (str): The search query.
            count (int): The number of results to return (max 20).

        Returns:
            dict: The JSON response from the Brave Search API.
        """
        if count > 20:
            count = 20 # Brave Search API limit

        params = {
            "q": query,
            "count": count
        }
        try:
            response = requests.get("https://api.search.brave.com/res/v1/web/search", headers=self.headers, params=params)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during Brave Search API call: {e}")
            return {"error": str(e)}

