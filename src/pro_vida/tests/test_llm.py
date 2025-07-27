import unittest
from unittest.mock import patch, MagicMock
from src.pro_vida.models import LLM

class TestLLM(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.endpoint = "http://test_endpoint"
        self.timeout = 10
        self.llm = LLM(self.api_key, self.endpoint, self.timeout)

    @patch('src.pro_vida.models.requests.post')
    def test_generate_text_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"text": "Generated text"}]}
        mock_post.return_value = mock_response

        prompt = "Test prompt"
        result = self.llm.generate_text(prompt)

        mock_post.assert_called_once_with(
            self.endpoint,
            json={"prompt": prompt},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout
        )
        self.assertEqual(result, "Generated text")

    @patch('src.pro_vida.models.requests.post')
    def test_generate_text_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        prompt = "Test prompt"
        with self.assertRaises(Exception):
            self.llm.generate_text(prompt)

    @patch('src.pro_vida.models.requests.post')
    def test_generate_text_invalid_input(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        prompt = ""
        with self.assertRaises(Exception):
            self.llm.generate_text(prompt)

if __name__ == "__main__":
    unittest.main()