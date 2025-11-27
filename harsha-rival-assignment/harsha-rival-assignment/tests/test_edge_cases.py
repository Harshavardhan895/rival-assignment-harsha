
import unittest
from function import analyze_api_logs

class EdgeCaseTests(unittest.TestCase):
    def test_invalid_timestamp(self):
        logs = [{"timestamp":"2025-13-01T00:00:00Z","endpoint":"/api/x","method":"GET","response_time_ms":100,"status_code":200}]
        out = analyze_api_logs(logs)
        self.assertEqual(out['summary']['total_requests'], 0)

    def test_negative_values(self):
        logs = [{"timestamp":"2025-01-15T10:00:00Z","endpoint":"/api/x","method":"GET","response_time_ms":-10,"status_code":200}]
        out = analyze_api_logs(logs)
        self.assertEqual(out['summary']['total_requests'], 0)

if __name__ == '__main__':
    unittest.main()
