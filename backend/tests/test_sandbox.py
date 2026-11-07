import unittest
from backend.sandbox.runner import run_tests_in_sandbox


class TestSandboxRunner(unittest.TestCase):
    def setUp(self):
        self.sample_tests = """
import unittest
from solution import add

class TestAdd(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(add(1, 2), 3)

    def test_negative(self):
        self.assertEqual(add(-1, -1), -2)

    def test_zero(self):
        self.assertEqual(add(0, 5), 5)

if __name__ == '__main__':
    unittest.main()
"""

    def test_passing_solution(self):
        files = {
            "solution.py": "def add(a, b):\n    return a + b\n"
        }
        res = run_tests_in_sandbox(files, self.sample_tests, timeout=5)
        self.assertTrue(res.passed)
        self.assertEqual(res.score, 1.0)
        self.assertEqual(res.passed_tests, 3)
        self.assertEqual(res.total_tests, 3)
        self.assertIsNone(res.error)

    def test_partially_failing_solution(self):
        # Passes test_positive (1+2=3), fails test_negative (-1+-1 != 3)
        files = {
            "solution.py": "def add(a, b):\n    if a == 1 and b == 2:\n        return 3\n    return 0\n"
        }
        res = run_tests_in_sandbox(files, self.sample_tests, timeout=5)
        self.assertFalse(res.passed)
        self.assertLess(res.score, 1.0)
        self.assertEqual(res.passed_tests, 1)
        self.assertEqual(res.total_tests, 3)

    def test_syntax_error(self):
        files = {
            "solution.py": "def add(a, b)\n    invalid syntax here"
        }
        res = run_tests_in_sandbox(files, self.sample_tests, timeout=5)
        self.assertFalse(res.passed)
        self.assertEqual(res.score, 0.0)
        self.assertIn("SyntaxError", res.stderr)

    def test_timeout_execution(self):
        files = {
            "solution.py": "def add(a, b):\n    while True:\n        pass\n"
        }
        res = run_tests_in_sandbox(files, self.sample_tests, timeout=1)
        self.assertFalse(res.passed)
        self.assertEqual(res.score, 0.0)
        self.assertIn("timed out", res.error)


if __name__ == "__main__":
    unittest.main()

