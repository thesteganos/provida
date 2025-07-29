import unittest
from unittest.mock import patch
from src.app.cli import main

class TestCLI(unittest.TestCase):
    @patch('src.app.cli.rapida')
    def test_rapida_command(self, mock_rapida):
        # Mock the rapida function to avoid actual execution
        mock_rapida.return_value = "Mocked response for rapida command"
        
        # Test the rapida command
        with self.assertLogs('src.app.cli', level='INFO') as log:
            main(['rapida', 'qual a dose recomendada de vitamina D para adultos?'])
        
        # Check if the rapida function was called with the correct argument
        mock_rapida.assert_called_with('qual a dose recomendada de vitamina D para adultos?')
        
        # Check if the correct log message was generated
        self.assertIn('Mocked response for rapida command', log.output)

if __name__ == '__main__':
    unittest.main()