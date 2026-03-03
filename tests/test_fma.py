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

    def test_rollback_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "script.py").write_text("print('x')", encoding="utf-8")

            planned = plan_moves(source, dest, rules={".py": "code"})
            undo = base / "undo.json"
            apply_moves(planned, undo, operation="move")

            restored = rollback_from_undo(undo)
            self.assertEqual(restored, 1)
            self.assertTrue((source / "script.py").exists())

    def test_rollback_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "script.py").write_text("print('x')", encoding="utf-8")

            planned = plan_moves(source, dest, rules={".py": "code"})
            undo = base / "undo.json"
            apply_moves(planned, undo, operation="copy")

            self.assertTrue((source / "script.py").exists())
            self.assertTrue((dest / "code" / "script.py").exists())

            restored = rollback_from_undo(undo)
            self.assertEqual(restored, 1)
            self.assertTrue((source / "script.py").exists())
            self.assertFalse((dest / "code" / "script.py").exists())

    def test_rollback_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "x.txt").write_text("hi", encoding="utf-8")

            planned = plan_moves(source, dest, rules={".txt": "documents"})
            undo = base / "undo.json"
            apply_moves(planned, undo)

            restored = rollback_from_undo(undo, dry_run=True)
            self.assertEqual(restored, 1)
            self.assertFalse((source / "x.txt").exists())
            self.assertTrue((dest / "documents" / "x.txt").exists())

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

    def test_include_exclude_and_max_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "src"
            dest = base / "sorted"
            source.mkdir()
            (source / "keep.py").write_text("x", encoding="utf-8")
            (source / "skip.log").write_text("x", encoding="utf-8")
            (source / "keep2.py").write_text("x", encoding="utf-8")

            planned = plan_moves(
                source,
                dest,
                rules={".py": "code", ".log": "logs"},
                include_patterns=["*.py", "*.log"],
                exclude_patterns=["skip.*"],
                max_files=1,
            )
            self.assertEqual(len(planned), 1)
            self.assertTrue(planned[0].source.endswith(".py"))




class TestQuickPresetDefaults(unittest.TestCase):
    def test_quick_preset_excludes_build_dirs(self):
        from fma.cli import DEFAULT_PROJECT_EXCLUDES

        self.assertIn("*/.next/*", DEFAULT_PROJECT_EXCLUDES)
        self.assertIn("*/node_modules/*", DEFAULT_PROJECT_EXCLUDES)


if __name__ == "__main__":
    unittest.main()
