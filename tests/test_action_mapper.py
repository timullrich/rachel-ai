import unittest

from src.gtaf.action_mapper import build_action_id


class TestActionMapper(unittest.TestCase):
    def test_false_is_unknown_not_read(self):
        action = build_action_id("execute_command", {"command": "false"})
        self.assertEqual("execute_command:unknown", action)

    def test_ls_is_filesystem_read(self):
        action = build_action_id("execute_command", {"command": "ls -la"})
        self.assertEqual("execute_command:filesystem_read", action)

    def test_rm_is_filesystem_write(self):
        action = build_action_id("execute_command", {"command": "rm test.txt"})
        self.assertEqual("execute_command:filesystem_write", action)


if __name__ == "__main__":
    unittest.main()
