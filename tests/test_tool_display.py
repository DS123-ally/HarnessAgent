import unittest

from forge.tool_display import summarize_tool_arguments


class ToolDisplayTests(unittest.TestCase):
    def test_write_file_summary_hides_long_content(self):
        summary = summarize_tool_arguments(
            "write_file",
            {
                "path": "calculator.py",
                "content": "def add(a, b):\n    return a + b\n" * 20,
            },
        )

        self.assertIn('path="calculator.py"', summary)
        self.assertIn("content=<text", summary)
        self.assertNotIn("return a + b\n", summary)

    def test_run_command_summary_shows_command(self):
        summary = summarize_tool_arguments(
            "run_command",
            {
                "command": "python calculator.py"
            },
        )

        self.assertEqual(
            summary,
            'run_command command="python calculator.py"',
        )


if __name__ == "__main__":
    unittest.main()
