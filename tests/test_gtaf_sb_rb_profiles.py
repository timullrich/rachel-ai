import unittest
from pathlib import Path

from gtaf_sdk.enforcement import enforce_from_files


class TestGtafSbRbProfiles(unittest.TestCase):
    def test_sb_api_only_profile_denies_with_outside_sb(self):
        repo_root = Path(__file__).resolve().parent.parent
        artifacts_dir = str(repo_root / "gtaf_artifacts")
        context = {
            "scope": "local:rachel",
            "component": "chat-service",
            "interface": "tool-calls",
            "action": "execute_command.date",
        }

        result = enforce_from_files(
            drc_path=str(repo_root / "gtaf_artifacts" / "drc_sb_api_only.json"),
            artifacts_dir=artifacts_dir,
            context=context,
            reload=True,
        )
        self.assertEqual("DENY", result.outcome)
        self.assertEqual("OUTSIDE_SB", result.reason_code)

    def test_rb_guest_only_profile_denies_with_rb_required(self):
        repo_root = Path(__file__).resolve().parent.parent
        artifacts_dir = str(repo_root / "gtaf_artifacts")
        context = {
            "scope": "local:rachel",
            "component": "chat-service",
            "interface": "tool-calls",
            "action": "execute_command.date",
        }

        result = enforce_from_files(
            drc_path=str(repo_root / "gtaf_artifacts" / "drc_rb_guest_only.json"),
            artifacts_dir=artifacts_dir,
            context=context,
            reload=True,
        )
        self.assertEqual("DENY", result.outcome)
        self.assertEqual("RB_REQUIRED", result.reason_code)

    def test_rb_multi_profile_allows_if_any_rb_active(self):
        repo_root = Path(__file__).resolve().parent.parent
        artifacts_dir = str(repo_root / "gtaf_artifacts")
        context = {
            "scope": "local:rachel",
            "component": "chat-service",
            "interface": "tool-calls",
            "action": "execute_command.date",
        }

        result = enforce_from_files(
            drc_path=str(repo_root / "gtaf_artifacts" / "drc_rb_multi.json"),
            artifacts_dir=artifacts_dir,
            context=context,
            reload=True,
        )
        self.assertEqual("EXECUTE", result.outcome)
        self.assertEqual("OK", result.reason_code)


if __name__ == "__main__":
    unittest.main()
