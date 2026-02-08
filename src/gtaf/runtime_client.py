"""Thin adapter around the official gtaf-runtime library."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from .artifact_loader import ArtifactLoader

try:
    from gtaf_runtime import EnforcementResult, enforce
except Exception:  # pragma: no cover - fail-safe path when plugin is unavailable
    enforce = None

    @dataclass(frozen=True)
    class EnforcementResult:  # type: ignore[no-redef]
        outcome: str
        drc_id: str | None
        revision: int | None
        valid_until: str | None
        reason_code: str
        refs: list[str]
        details: dict


@dataclass(frozen=True)
class GtafRuntimeConfig:
    artifact_dir: str
    scope: str
    component: str
    interface: str
    system: str = "rachel-local-agent"
    default_user: str = "unknown"
    default_mode: str = "text"


class GtafRuntimeClient:
    """Calls gtaf-runtime enforce() with loaded artifacts and normalized context."""

    def __init__(self, config: GtafRuntimeConfig, loader: Optional[ArtifactLoader] = None):
        self.config = config
        self.loader = loader or ArtifactLoader(artifact_dir=config.artifact_dir)

    def enforce(self, action: str, context: Optional[dict] = None) -> EnforcementResult:
        context = context or {}

        if not isinstance(action, str) or not action:
            return self._deny("INVALID_ACTION")

        if enforce is None:
            return self._deny("RUNTIME_UNAVAILABLE")

        try:
            loaded = self.loader.load(force_reload=bool(context.get("reload_artifacts")))
        except Exception as error:
            return self._deny("GTAF_ARTIFACT_LOAD_FAILED", details={"error": str(error)})

        runtime_context = {
            "action": action,
            "scope": context.get("scope", self.config.scope),
            "component": context.get("component", self.config.component),
            "interface": context.get("interface", self.config.interface),
            "system": context.get("system", self.config.system),
            "mode": context.get("mode", self.config.default_mode),
            "user": context.get("user", self.config.default_user),
        }

        try:
            return enforce(drc=loaded.drc, context=runtime_context, artifacts=loaded.artifacts)
        except Exception as error:
            return self._deny("GTAF_RUNTIME_ERROR", details={"error": str(error)})

    def warmup(self) -> EnforcementResult:
        """Validates runtime availability and artifact loading during app startup."""
        if enforce is None:
            return self._deny("RUNTIME_UNAVAILABLE")

        try:
            loaded = self.loader.load(force_reload=True)
        except Exception as error:
            return self._deny("GTAF_ARTIFACT_LOAD_FAILED", details={"error": str(error)})

        return EnforcementResult(
            outcome="EXECUTE",
            drc_id=loaded.drc.get("id"),
            revision=loaded.drc.get("revision"),
            valid_until=loaded.drc.get("valid_until"),
            reason_code="WARMUP_OK",
            refs=[],
            details={},
        )

    def _deny(self, reason_code: str, details: Optional[dict] = None) -> EnforcementResult:
        return EnforcementResult(
            outcome="DENY",
            drc_id=None,
            revision=None,
            valid_until=datetime.now(UTC).isoformat(),
            reason_code=reason_code,
            refs=[],
            details=details or {},
        )
