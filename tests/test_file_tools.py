import tempfile
import unittest
from pathlib import Path

from forge.tools.files import (
    CreateDirectoryTool,
    DeleteDirectoryTool,
    DeleteFileTool,
    EditFileTool,
    ListFilesTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)


class FileToolSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_file_rejects_path_outside_project_root(self):
        outside_file = self.project_root.parent / "outside.txt"
        outside_file.write_text("secret", encoding="utf-8")
        self.addCleanup(outside_file.unlink)

        result = ReadFileTool(
            project_root=self.project_root
        ).execute(path="../outside.txt")

        self.assertFalse(result["success"])
        self.assertIn("outside the project root", result["error"])

    def test_write_edit_search_list_and_delete_stay_inside_project_root(self):
        writer = WriteFileTool(project_root=self.project_root)
        editor = EditFileTool(project_root=self.project_root)
        searcher = SearchFilesTool(project_root=self.project_root)
        reader = ReadFileTool(project_root=self.project_root)
        lister = ListFilesTool(project_root=self.project_root)
        deleter = DeleteFileTool(project_root=self.project_root)

        write_result = writer.execute(
            path="notes/example.txt",
            content="hello harness",
        )
        self.assertTrue(write_result["success"])
        self.assertEqual(write_result["path"], "notes\\example.txt")

        edit_result = editor.execute(
            path="notes/example.txt",
            old_text="hello",
            new_text="hi",
        )
        self.assertTrue(edit_result["success"])

        read_result = reader.execute(path="notes/example.txt")
        self.assertTrue(read_result["success"])
        self.assertEqual(read_result["content"], "hi harness")

        search_result = searcher.execute(
            path=".",
            query="harness",
        )
        self.assertTrue(search_result["success"])
        self.assertEqual(search_result["results"][0]["file"], "notes\\example.txt")

        list_result = lister.execute(path="notes")
        self.assertTrue(list_result["success"])
        self.assertEqual(list_result["items"][0]["name"], "example.txt")

        delete_result = deleter.execute(path="notes/example.txt")
        self.assertTrue(delete_result["success"])
        self.assertFalse((self.project_root / "notes/example.txt").exists())

    def test_create_directory_stays_inside_project_root(self):
        creator = CreateDirectoryTool(project_root=self.project_root)

        result = creator.execute(path="dinesh")

        self.assertTrue(result["success"])
        self.assertTrue((self.project_root / "dinesh").is_dir())

        outside_result = creator.execute(path="../outside-folder")

        self.assertFalse(outside_result["success"])
        self.assertIn("outside the project root", outside_result["error"])

    def test_delete_directory_stays_inside_project_root(self):
        folder = self.project_root / "empty-folder"
        folder.mkdir()
        deleter = DeleteDirectoryTool(project_root=self.project_root)

        result = deleter.execute(path="empty-folder")

        self.assertTrue(result["success"])
        self.assertFalse(folder.exists())

        outside_result = deleter.execute(path="../outside-folder")

        self.assertFalse(outside_result["success"])
        self.assertIn("outside the project root", outside_result["error"])

    def test_delete_directory_requires_recursive_for_non_empty_folder(self):
        folder = self.project_root / "notes"
        folder.mkdir()
        (folder / "example.txt").write_text("hello", encoding="utf-8")
        deleter = DeleteDirectoryTool(project_root=self.project_root)

        blocked_result = deleter.execute(path="notes")

        self.assertFalse(blocked_result["success"])
        self.assertIn("recursive=true", blocked_result["error"])
        self.assertTrue(folder.exists())

        result = deleter.execute(path="notes", recursive=True)

        self.assertTrue(result["success"])
        self.assertFalse(folder.exists())


if __name__ == "__main__":
    unittest.main()
