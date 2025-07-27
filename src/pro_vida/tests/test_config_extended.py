import unittest
import os
from unittest.mock import patch
from src.pro_vida.config.settings import load_config

class TestLoadConfigExtended(unittest.TestCase):

    @patch.dict(os.environ, {"NEO4J_PASSWORD": "secret"})
    def test_env_var_expansion(self):
        cfg = load_config()
        self.assertEqual(
            cfg["services"]["neo4j_knowledge"]["password"],
            "secret"
        )

    @patch.dict(os.environ, {"NEO4J_PORT": "7687"})
    def test_env_var_expansion_int(self):
        cfg = load_config()
        self.assertEqual(
            cfg["services"]["neo4j_knowledge"]["port"],
            7687
        )

    @patch.dict(os.environ, {"NEO4J_ENABLED": "true"})
    def test_env_var_expansion_bool(self):
        cfg = load_config()
        self.assertTrue(
            cfg["services"]["neo4j_knowledge"]["enabled"]
        )

    @patch.dict(os.environ, {"NEO4J_PASSWORD": ""})
    def test_missing_env_var(self):
        cfg = load_config()
        self.assertEqual(
            cfg["services"]["neo4j_knowledge"]["password"],
            "default_password"
        )

    @patch.dict(os.environ, {"NEO4J_PORT": "invalid"})
    def test_invalid_env_var(self):
        with self.assertRaises(ValueError):
            load_config()

if __name__ == "__main__":
    unittest.main()