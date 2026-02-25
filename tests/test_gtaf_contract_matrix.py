import unittest
from pathlib import Path

from gtaf_sdk.enforcement import enforce_from_files


class TestGtafContractMatrix(unittest.TestCase):
    def test_profile_action_contract_matrix(self):
        repo_root = Path(__file__).resolve().parent.parent
        artifacts_dir = str(repo_root / "gtaf_artifacts")
        base_context = {
            "scope": "local:rachel",
            "component": "chat-service",
            "interface": "tool-calls",
        }

        cases = [
            ("drc.json", "execute_command.date", "EXECUTE", "OK"),
            ("drc.json", "execute_command.rm", "DENY", "DR_MISMATCH"),
            ("drc_day.json", "email_operations.send", "EXECUTE", "OK"),
            ("drc_night.json", "email_operations.send", "DENY", "DR_MISMATCH"),
            ("drc_sb_api_only.json", "execute_command.date", "DENY", "OUTSIDE_SB"),
            ("drc_rb_guest_only.json", "execute_command.date", "DENY", "RB_REQUIRED"),
            ("drc_rb_multi.json", "execute_command.date", "EXECUTE", "OK"),
        ]

        for drc_name, action, expected_outcome, expected_reason in cases:
            with self.subTest(drc=drc_name, action=action):
                result = enforce_from_files(
                    drc_path=str(repo_root / "gtaf_artifacts" / drc_name),
                    artifacts_dir=artifacts_dir,
                    context={**base_context, "action": action},
                    reload=True,
                )
                self.assertEqual(expected_outcome, result.outcome)
                self.assertEqual(expected_reason, result.reason_code)


if __name__ == "__main__":
    unittest.main()
