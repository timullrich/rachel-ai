import unittest

from gtaf_sdk.actions import UNKNOWN_ACTION_ID

from src.gtaf.action_mapper import build_action_id


class TestActionMapper(unittest.TestCase):
    def test_execute_command_uses_first_token(self):
        action = build_action_id("execute_command", {"command": "rm test.txt"})
        self.assertEqual("execute_command.rm", action)

    def test_execute_command_date(self):
        action = build_action_id("execute_command", {"command": "date"})
        self.assertEqual("execute_command.date", action)

    def test_non_command_tool_returns_prefix(self):
        action = build_action_id("weather_operations", {"operation": "get_weather"})
        self.assertEqual("weather_operations", action)

    def test_unmapped_tool_returns_unknown(self):
        action = build_action_id("custom_tool", {"command": "run"})
        self.assertEqual(UNKNOWN_ACTION_ID, action)


if __name__ == "__main__":
    unittest.main()
