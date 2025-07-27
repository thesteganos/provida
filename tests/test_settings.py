import os
import unittest
from unittest.mock import patch
import importlib
from src import settings
from src.settings import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, API_KEY

class TestSettings(unittest.TestCase):
    @patch.dict(os.environ, {"EMAIL_HOST": "test.smtp.com", "EMAIL_PORT": "25", "EMAIL_USER": "testuser", "EMAIL_PASSWORD": "testpass", "API_KEY": "testapikey"})
    def test_settings_loaded_from_env(self):
        import importlib
        import src.settings
        importlib.reload(src.settings)
        from src.settings import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, API_KEY
        self.assertEqual(EMAIL_HOST, "test.smtp.com")
        self.assertEqual(EMAIL_PORT, 25)
        self.assertEqual(EMAIL_USER, "testuser")
        self.assertEqual(EMAIL_PASSWORD, "testpass")
        self.assertEqual(API_KEY, "testapikey")

    def test_settings_default_values(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(EMAIL_HOST, "smtp.example.com")
            self.assertEqual(EMAIL_PORT, 587)
            self.assertEqual(EMAIL_USER, "user@example.com")
            self.assertEqual(EMAIL_PASSWORD, "password")
            self.assertEqual(API_KEY, "your_api_key_here")

    def test_settings_invalid_email_port(self):
        with patch.dict(os.environ, {"EMAIL_PORT": "invalid"}):
            with self.assertRaises(ValueError):
                int(os.getenv('EMAIL_PORT', 587))

    def test_settings_missing_email_host(self):
        with patch.dict(os.environ, {"EMAIL_HOST": ""}):
            self.assertEqual(EMAIL_HOST, "smtp.example.com")

    def test_settings_missing_email_port(self):
        with patch.dict(os.environ, {"EMAIL_PORT": ""}):
            self.assertEqual(EMAIL_PORT, 587)

    def test_settings_missing_email_user(self):
        with patch.dict(os.environ, {"EMAIL_USER": ""}):
            self.assertEqual(EMAIL_USER, "user@example.com")

    def test_settings_missing_email_password(self):
        with patch.dict(os.environ, {"EMAIL_PASSWORD": ""}):
            self.assertEqual(EMAIL_PASSWORD, "password")

    def test_settings_missing_api_key(self):
        with patch.dict(os.environ, {"API_KEY": ""}):
            self.assertEqual(API_KEY, "your_api_key_here")

    if __name__ == '__main__':
        unittest.main()