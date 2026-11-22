import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class StreamlitSmokeTests(unittest.TestCase):
    def test_dashboard_renders_without_exceptions(self):
        entrypoint = Path(__file__).resolve().parents[1] / "streamlit_app.py"
        app = AppTest.from_file(str(entrypoint)).run(timeout=60)
        errors = [item.message for item in app.exception]
        self.assertEqual(errors, [], "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
