import unittest
from unittest.mock import patch
import os

class TestLoadConfig(unittest.TestCase):
    @patch.dict(os.environ, {"NEO4J_PASSWORD": "secret"})
    def test_env_var_expansion(self):
        from pro_vida.config.settings import load_config
        cfg = load_config()
        self.assertEqual(
            cfg["services"]["neo4j_knowledge"]["password"],
            "secret"
        )

if __name__ == "__main__":
    unittest.main()
