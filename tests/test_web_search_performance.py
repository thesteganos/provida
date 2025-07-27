import unittest
import time
import statistics
from src.app.tools.web_search import search_web

class TestWebSearchPerformance(unittest.TestCase):
    def setUp(self):
        self.search_queries = [
            ("Python programming", "general", 5),
            ("Machine learning", "academic", 5),
            ("research on climate change", "auto", 5)
        ]
        self.execution_times = []

    def test_search_web_performance(self):
        for query, search_type, count in self.search_queries:
            start_time = time.time()
            search_web(query, search_type=search_type, count=count)
            time.sleep(2)  # Add a 2-second delay
            end_time = time.time()
            execution_time = end_time - start_time
            self.execution_times.append(execution_time)
            self.assertLess(execution_time, 5, f"Search took too long: {execution_time} seconds")

    def tearDown(self):
        if self.execution_times:
            avg_time = statistics.mean(self.execution_times)
            max_time = max(self.execution_times)
            min_time = min(self.execution_times)
            num_requests = len(self.execution_times)
            success_rate = (num_requests / len(self.search_queries)) * 100

            print(f"Performance Report:")
            print(f"Average Execution Time: {avg_time:.2f} seconds")
            print(f"Maximum Execution Time: {max_time:.2f} seconds")
            print(f"Minimum Execution Time: {min_time:.2f} seconds")
            print(f"Number of Requests: {num_requests}")
            print(f"Success Rate: {success_rate:.2f}%")

if __name__ == '__main__':
    unittest.main()