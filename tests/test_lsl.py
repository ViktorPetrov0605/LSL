import unittest
from unittest.mock import patch, mock_open
import subprocess
import sys
import os
import lsl  # Adjust the import if needed (e.g., `import .lsl` for Python 3.3+)

class TestLSL(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="alpine = alpine:latest\nnginx = nginx:stable")
    def test_load_config(self, mock_file):
        config = lsl.load_config()
        self.assertEqual(config["alpine"], "alpine:latest")
        self.assertEqual(config["nginx"], "nginx:stable")

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_args_list(self, mock_parse_args):
        mock_parse_args.return_value = type('Args', (), {
            "list": True,
            "name": None,
            "net": False,
            "persist": False
        })
        with self.assertLogs() as log:
            lsl.main()
            self.assertIn("alpine: alpine:latest", log.output[0])

    @patch("subprocess.run")
    @patch("os.makedirs")
    def test_start_container(self, mock_makedirs, mock_run):
        with patch("lsl.load_config", return_value={"alpine": "alpine:latest"}):
            with patch("sys.argv", ["lsl.py", "-n", "alpine", "--net", "-p"]):
                lsl.main()
                expected_cmd = [
                    'docker', 'run', '-it', '--rm',
                    '--network', 'host',
                    f'-v {os.getcwd()}/.lsl_persist_alpine:/data',
                    'alpine:latest', '/bin/bash'
                ]
                mock_run.assert_called_with(expected_cmd, check=True)

    def test_invalid_container_name(self):
        with patch("sys.argv", ["lsl.py", "-n", "invalid"]):
            with self.assertRaises(SystemExit):
                lsl.main()

if __name__ == "__main__":
    unittest.main()
