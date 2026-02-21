import json
import tempfile
import unittest
from pathlib import Path

from src.gtaf.runtime_client import GtafRuntimeClient, GtafRuntimeConfig


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_valid_artifacts(base_dir: Path) -> tuple[str, str]:
    drc_path = base_dir / "drc.json"
    (base_dir / "sb").mkdir(parents=True, exist_ok=True)
    (base_dir / "dr").mkdir(parents=True, exist_ok=True)
    (base_dir / "rb").mkdir(parents=True, exist_ok=True)

    sb = {
        "id": "SB-LOCAL-RACHEL",
        "scope": "local:rachel",
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2030-01-01T00:00:00Z",
        "included_components": ["chat-service"],
        "excluded_components": [],
        "allowed_interfaces": ["tool-calls"],
    }
    dr = {
        "id": "DR-COMMAND-EXEC",
        "scope": "local:rachel",
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2030-01-01T00:00:00Z",
        "delegation_mode": "AUTONOMOUS",
        "decisions": ["execute_command.date"],
    }
    rb = {
        "id": "RB-TIM-LOCAL",
        "scope": "local:rachel",
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2030-01-01T00:00:00Z",
        "active": True,
    }
    drc = {
        "id": "DRC-LOCAL-RACHEL",
        "revision": 1,
        "result": "PERMITTED",
        "gtaf_ref": {"version": "0.1"},
        "scope": "local:rachel",
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2030-01-01T00:00:00Z",
        "refs": {
            "sb": ["SB-LOCAL-RACHEL"],
            "dr": ["DR-COMMAND-EXEC"],
            "rb": ["RB-TIM-LOCAL"],
        },
    }

    _write_json(base_dir / "sb" / "SB-LOCAL-RACHEL.json", sb)
    _write_json(base_dir / "dr" / "DR-COMMAND-EXEC.json", dr)
    _write_json(base_dir / "rb" / "RB-TIM-LOCAL.json", rb)
    _write_json(drc_path, drc)

    return str(drc_path), str(base_dir)


class TestGtafRuntimeClient(unittest.TestCase):
    def test_missing_artifacts_fail_safe_deny_with_sdk_code(self):
        config = GtafRuntimeConfig(
            drc_path="/tmp/does-not-exist-gtaf/drc.json",
            artifacts_dir="/tmp/does-not-exist-gtaf",
            scope="local:rachel",
            component="chat-service",
            interface="tool-calls",
        )
        client = GtafRuntimeClient(config)
        decision = client.enforce(action="execute_command.date")

        self.assertEqual("DENY", decision.outcome)
        self.assertTrue(decision.reason_code.startswith("SDK_"))

    def test_warmup_missing_artifacts_returns_not_ok(self):
        config = GtafRuntimeConfig(
            drc_path="/tmp/does-not-exist-gtaf/drc.json",
            artifacts_dir="/tmp/does-not-exist-gtaf",
            scope="local:rachel",
            component="chat-service",
            interface="tool-calls",
        )
        client = GtafRuntimeClient(config)
        result = client.warmup()

        self.assertFalse(result.ok)
        self.assertGreater(len(result.errors), 0)

    def test_allow_and_deny_via_sdk_client(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            drc_path, artifacts_dir = _create_valid_artifacts(Path(tmpdir))
            config = GtafRuntimeConfig(
                drc_path=drc_path,
                artifacts_dir=artifacts_dir,
                scope="local:rachel",
                component="chat-service",
                interface="tool-calls",
            )
            client = GtafRuntimeClient(config)

            allow = client.enforce(action="execute_command.date")
            deny = client.enforce(action="execute_command.rm")

            self.assertEqual("EXECUTE", allow.outcome)
            self.assertEqual("DENY", deny.outcome)


if __name__ == "__main__":
    unittest.main()
