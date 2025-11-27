
import unittest
import time
from function import analyze_api_logs
from utils import generate_sample_logs

class CoreFunctionTests(unittest.TestCase):
    def test_empty_input(self):
        out = analyze_api_logs([])
        self.assertEqual(out['summary']['total_requests'], 0)
        self.assertEqual(out['endpoint_stats'], [])

    def test_single_entry(self):
        logs = [{
            "timestamp":"2025-01-15T10:00:00Z",
            "endpoint":"/api/users",
            "method":"GET",
            "response_time_ms":120,
            "status_code":200,
            "user_id":"user_001",
            "request_size_bytes":256,
            "response_size_bytes":1024
        }]
        out = analyze_api_logs(logs)
        self.assertEqual(out['summary']['total_requests'], 1)
        self.assertEqual(out['endpoint_stats'][0]['request_count'], 1)

    def test_malformed_entries(self):
        logs = [
            {"timestamp":"invalid","endpoint":"/api/x","response_time_ms":100,"status_code":200},
            {"endpoint":"/api/x","response_time_ms":-5,"status_code":200},
            None
        ]
        out = analyze_api_logs(logs)
        self.assertEqual(out['summary']['total_requests'], 0)

    def test_performance_10k(self):
        logs = generate_sample_logs(10000)
        start = time.time()
        out = analyze_api_logs(logs)
        duration = time.time() - start
        # performance target: process 10k logs in under 2 seconds on decent machines.
        self.assertTrue(duration < 2.5, f"Processing too slow: {duration}s")
        self.assertGreater(out['summary']['total_requests'], 0)

if __name__ == '__main__':
    unittest.main()
