"""SDK-only GTAF integration client for Rachel AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from gtaf_sdk.enforcement import enforce_from_files
from gtaf_sdk.models import RuntimeContext
from gtaf_sdk.validation import ValidationResult, warmup_from_files


@dataclass(frozen=True)
class GtafRuntimeConfig:
    drc_path: str
    artifacts_dir: str
    scope: str
    component: str
    interface: str
    system: str = "rachel-local-agent"
    default_user: str = "unknown"
    default_mode: str = "text"


class GtafRuntimeClient:
    """Delegates warmup/enforcement exclusively to gtaf-sdk-py."""

    def __init__(self, config: GtafRuntimeConfig):
        self.config = config

    def warmup(self, reload: bool = True) -> ValidationResult:
        return warmup_from_files(
            drc_path=self.config.drc_path,
            artifacts_dir=self.config.artifacts_dir,
            reload=reload,
        )

    def enforce(self, action: str, context: Optional[Dict[str, Any]] = None) -> Any:
        context = context or {}
        runtime_context = RuntimeContext(
            scope=context.get("scope", self.config.scope),
            component=context.get("component", self.config.component),
            interface=context.get("interface", self.config.interface),
            action=action,
            extras={
                "system": context.get("system", self.config.system),
                "mode": context.get("mode", self.config.default_mode),
                "user": context.get("user", self.config.default_user),
            },
        ).to_dict()

        return enforce_from_files(
            drc_path=self.config.drc_path,
            artifacts_dir=self.config.artifacts_dir,
            context=runtime_context,
        )
