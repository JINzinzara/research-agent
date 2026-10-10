"""Check that module imports and offline replay do not require API credentials."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


class ImportTests(unittest.TestCase):
    """Check lazy SDK initialization in a clean child process."""

    def test_imports_without_keys_or_provider_clients(self):
        environment = os.environ.copy()
        for name in ("OPENAI_API_KEY", "COINGECKO_API_KEY"):
            environment.pop(name, None)
        root = Path(__file__).resolve().parents[1]
        environment["PYTHONPATH"] = str(root / "src")
        code = (
            "import sys; "
            "from research_agent import agent, collectors, generation; "
            "assert collectors._price_client.cache_info().currsize == 0; "
            "assert generation._llm_client.cache_info().currsize == 0; "
            "assert 'openai' not in sys.modules; "
            "assert 'coingecko_sdk' not in sys.modules"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            env=environment,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
