import json
import tempfile
import unittest
from pathlib import Path

from gtaf_sdk.enforcement import enforce_from_files


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _build_fixture(base_dir: Path) -> tuple[str, str]:
    drc_path = base_dir / "drc.json"
    (base_dir / "sb").mkdir(parents=True, exist_ok=True)
    (base_dir / "dr").mkdir(parents=True, exist_ok=True)
    (base_dir / "rb").mkdir(parents=True, exist_ok=True)

    _write_json(
        base_dir / "sb" / "SB-LOCAL-RACHEL.json",
        {
            "id": "SB-LOCAL-RACHEL",
            "scope": "local:rachel",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_until": "2030-01-01T00:00:00Z",
            "included_components": ["chat-service"],
            "excluded_components": [],
            "allowed_interfaces": ["tool-calls"],
        },
    )
    _write_json(
        base_dir / "dr" / "DR-COMMAND-EXEC.json",
        {
            "id": "DR-COMMAND-EXEC",
            "scope": "local:rachel",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_until": "2030-01-01T00:00:00Z",
            "delegation_mode": "AUTONOMOUS",
            "decisions": ["execute_command.date"],
        },
    )
    _write_json(
        base_dir / "rb" / "RB-TIM-LOCAL.json",
        {
            "id": "RB-TIM-LOCAL",
            "scope": "local:rachel",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_until": "2030-01-01T00:00:00Z",
            "active": True,
        },
    )
    _write_json(
        drc_path,
        {
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
        },
    )

    return str(drc_path), str(base_dir)


class TestSdkIntegration(unittest.TestCase):
    def test_real_enforce_from_files_allow_deny_and_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            drc_path, artifacts_dir = _build_fixture(Path(tmpdir))
            context = {
                "scope": "local:rachel",
                "component": "chat-service",
                "interface": "tool-calls",
                "action": "execute_command.date",
            }

            allow = enforce_from_files(
                drc_path=drc_path,
                artifacts_dir=artifacts_dir,
                context=context,
            )
            self.assertEqual("EXECUTE", allow.outcome)

            deny = enforce_from_files(
                drc_path=drc_path,
                artifacts_dir=artifacts_dir,
                context={**context, "action": "execute_command.rm"},
            )
            self.assertEqual("DENY", deny.outcome)

            Path(artifacts_dir, "dr", "DR-COMMAND-EXEC.json").unlink()
            missing = enforce_from_files(
                drc_path=drc_path,
                artifacts_dir=artifacts_dir,
                context=context,
                reload=True,
            )
            self.assertEqual("DENY", missing.outcome)
            self.assertEqual("SDK_ARTIFACT_NOT_FOUND", missing.reason_code)


if __name__ == "__main__":
    unittest.main()
