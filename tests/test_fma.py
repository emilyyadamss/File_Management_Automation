import json
import tempfile
import unittest
from pathlib import Path

from fma.organizer import apply_moves, plan_moves, rollback_from_undo


class TestFMA(unittest.TestCase):
    def test_plan_and_apply_extension_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "a.jpg").write_text("x", encoding="utf-8")
            (source / "b.pdf").write_text("x", encoding="utf-8")

            planned = plan_moves(source, dest, rules={".jpg": "images", ".pdf": "documents"})
            self.assertEqual(len(planned), 2)

            undo = base / "undo.json"
            moved = apply_moves(planned, undo)
            self.assertEqual(moved, 2)
            self.assertTrue((dest / "images" / "a.jpg").exists())
            self.assertTrue((dest / "documents" / "b.pdf").exists())
            self.assertTrue(undo.exists())

            payload = json.loads(undo.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["moves"]), 2)

    def test_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "script.py").write_text("print('x')", encoding="utf-8")

            planned = plan_moves(source, dest, rules={".py": "code"})
            undo = base / "undo.json"
            apply_moves(planned, undo)

            restored = rollback_from_undo(undo)
            self.assertEqual(restored, 1)
            self.assertTrue((source / "script.py").exists())

    def test_date_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "note.txt").write_text("hi", encoding="utf-8")

            planned = plan_moves(source, dest, rules={}, mode="date")
            self.assertEqual(len(planned), 1)
            self.assertIn("modified date", planned[0].reason)


if __name__ == "__main__":
    unittest.main()
