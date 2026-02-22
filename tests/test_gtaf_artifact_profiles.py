import unittest
from pathlib import Path

from gtaf_sdk.enforcement import enforce_from_files


class TestGtafArtifactProfiles(unittest.TestCase):
    def test_email_send_allowed_day_denied_night(self):
        repo_root = Path(__file__).resolve().parent.parent
        artifacts_dir = str(repo_root / "gtaf_artifacts")
        context = {
            "scope": "local:rachel",
            "component": "chat-service",
            "interface": "tool-calls",
            "action": "email_operations.send",
        }

        day = enforce_from_files(
            drc_path=str(repo_root / "gtaf_artifacts" / "drc_day.json"),
            artifacts_dir=artifacts_dir,
            context=context,
            reload=True,
        )
        self.assertEqual("EXECUTE", day.outcome)

        night = enforce_from_files(
            drc_path=str(repo_root / "gtaf_artifacts" / "drc_night.json"),
            artifacts_dir=artifacts_dir,
            context=context,
            reload=True,
        )
        self.assertEqual("DENY", night.outcome)
        self.assertEqual("DR_MISMATCH", night.reason_code)


if __name__ == "__main__":
    unittest.main()
