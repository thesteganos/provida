import unittest
from unittest.mock import patch, MagicMock
from src.app.tools.web_search import search_web

class TestWebSearch(unittest.TestCase):
    @patch('src.app.tools.web_search.BraveSearch')
    @patch('src.app.tools.web_search.PubMedSearch')
    def test_search_web_general(self, mock_pubmed_search, mock_brave_search):
        mock_brave_search_instance = mock_brave_search.return_value
        mock_brave_search_instance.search.return_value = [{'title': 'General Result 1'}, {'title': 'General Result 2'}]
        
        result = search_web("test query", search_type="general", count=2)
        
        mock_brave_search_instance.search.assert_called_once_with("test query", count=2)
        self.assertEqual(result, [{'title': 'General Result 1'}, {'title': 'General Result 2'}])

    @patch('src.app.tools.web_search.BraveSearch')
    @patch('src.app.tools.web_search.PubMedSearch')
    def test_search_web_academic(self, mock_pubmed_search, mock_brave_search):
        mock_pubmed_search_instance = mock_pubmed_search.return_value
        mock_pubmed_search_instance.search.return_value = [{'title': 'Academic Result 1'}, {'title': 'Academic Result 2'}]
        
        result = search_web("test query", search_type="academic", count=2)
        
        mock_pubmed_search_instance.search.assert_called_once_with("test query", count=2)
        self.assertEqual(result, [{'title': 'Academic Result 1'}, {'title': 'Academic Result 2'}])

    @patch('src.app.tools.web_search.BraveSearch')
    @patch('src.app.tools.web_search.PubMedSearch')
    def test_search_web_auto_academic(self, mock_pubmed_search, mock_brave_search):
        mock_pubmed_search_instance = mock_pubmed_search.return_value
        mock_pubmed_search_instance.search.return_value = [{'title': 'Auto Academic Result 1'}, {'title': 'Auto Academic Result 2'}]
        
        result = search_web("test query with academic keyword", search_type="auto", count=2)
        
        mock_pubmed_search_instance.search.assert_called_once_with("test query with academic keyword", count=2)
        self.assertEqual(result, [{'title': 'Auto Academic Result 1'}, {'title': 'Auto Academic Result 2'}])

    @patch('src.app.tools.web_search.BraveSearch')
    @patch('src.app.tools.web_search.PubMedSearch')
    def test_search_web_auto_general(self, mock_pubmed_search, mock_brave_search):
        mock_brave_search_instance = mock_brave_search.return_value
        mock_brave_search_instance.search.return_value = [{'title': 'Auto General Result 1'}, {'title': 'Auto General Result 2'}]
        
        result = search_web("test query", search_type="auto", count=2)
        
        mock_brave_search_instance.search.assert_called_once_with("test query", count=2)
        self.assertEqual(result, [{'title': 'Auto General Result 1'}, {'title': 'Auto General Result 2'}])

    def test_search_web_invalid_search_type(self):
        with self.assertRaises(ValueError) as context:
            search_web("test query", search_type="invalid")
        
        self.assertEqual(str(context.exception), "Invalid search type: invalid")

if __name__ == '__main__':
    unittest.main()