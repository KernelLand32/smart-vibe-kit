import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pocket_list import DataError, add_task, load_tasks, main  # noqa: E402


class AddTaskTests(unittest.TestCase):
    def test_add_persists_and_ids_continue_after_reload(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "tasks.json"
            first = add_task(data, "Buy tea")
            second = add_task(data, "Call Sam")
            self.assertEqual(first["id"], 1)
            self.assertEqual(second["id"], 2)
            self.assertEqual(load_tasks(data), [first, second])

    def test_blank_text_fails_without_changing_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "tasks.json"
            add_task(data, "Existing")
            before = data.read_bytes()
            stderr = StringIO()
            with redirect_stderr(stderr):
                code = main(["--data", str(data), "add", "   "])
            self.assertEqual(code, 2)
            self.assertIn("Task text is required", stderr.getvalue())
            self.assertEqual(data.read_bytes(), before)

    def test_malformed_data_is_reported_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "tasks.json"
            data.write_text("{broken", encoding="utf-8")
            before = data.read_bytes()
            with self.assertRaises(DataError):
                add_task(data, "New task")
            self.assertEqual(data.read_bytes(), before)

    def test_cli_reports_added_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "tasks.json"
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["--data", str(data), "add", "Buy tea"])
            self.assertEqual(code, 0)
            self.assertEqual(stdout.getvalue().strip(), "Added 1: Buy tea")
            stored = json.loads(data.read_text(encoding="utf-8"))
            self.assertEqual(stored[0]["text"], "Buy tea")


if __name__ == "__main__":
    unittest.main()
