import tempfile
import unittest
from pathlib import Path

from src.gtaf.artifact_loader import ArtifactLoader
from src.gtaf.runtime_client import GtafRuntimeClient, GtafRuntimeConfig


class TestArtifactLoader(unittest.TestCase):
    def test_missing_artifact_file_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ArtifactLoader(artifact_dir=tmpdir)
            with self.assertRaises(FileNotFoundError):
                loader.load()

    def test_malformed_yaml_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            (base / "DRC-LOCAL-RACHEL.yaml").write_text("[]\n", encoding="utf-8")
            (base / "SB-LOCAL-RACHEL.yaml").write_text("id: SB-1\n", encoding="utf-8")
            (base / "DR-COMMAND-EXEC.yaml").write_text("id: DR-1\n", encoding="utf-8")
            (base / "RB-TIM-LOCAL.yaml").write_text("id: RB-1\n", encoding="utf-8")

            loader = ArtifactLoader(artifact_dir=tmpdir)
            with self.assertRaises(ValueError):
                loader.load()


class TestGtafRuntimeClient(unittest.TestCase):
    def test_missing_artifacts_fail_safe_deny(self):
        config = GtafRuntimeConfig(
            artifact_dir="/tmp/does-not-exist-gtaf",
            scope="local:rachel",
            component="chat-service",
            interface="tool-calls",
        )
        client = GtafRuntimeClient(config)
        decision = client.enforce(action="execute_command:filesystem_write")

        self.assertEqual("DENY", decision.outcome)
        self.assertEqual("GTAF_ARTIFACT_LOAD_FAILED", decision.reason_code)

    def test_warmup_missing_artifacts_returns_deny(self):
        config = GtafRuntimeConfig(
            artifact_dir="/tmp/does-not-exist-gtaf",
            scope="local:rachel",
            component="chat-service",
            interface="tool-calls",
        )
        client = GtafRuntimeClient(config)
        decision = client.warmup()

        self.assertEqual("DENY", decision.outcome)
        self.assertEqual("GTAF_ARTIFACT_LOAD_FAILED", decision.reason_code)


if __name__ == "__main__":
    unittest.main()
