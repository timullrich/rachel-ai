"""Load GTAF artifacts from local YAML files with caching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(frozen=True)
class LoadedArtifacts:
    drc: Dict[str, Any]
    artifacts: Dict[str, Dict[str, Any]]


class ArtifactLoader:
    """Loads and validates GTAF artifacts from disk."""

    def __init__(
        self,
        artifact_dir: str,
        drc_file: str = "DRC-LOCAL-RACHEL.yaml",
        sb_file: str = "SB-LOCAL-RACHEL.yaml",
        dr_file: str = "DR-COMMAND-EXEC.yaml",
        rb_file: str = "RB-TIM-LOCAL.yaml",
    ) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.drc_file = drc_file
        self.sb_file = sb_file
        self.dr_file = dr_file
        self.rb_file = rb_file
        self._cache: LoadedArtifacts | None = None

    def load(self, force_reload: bool = False) -> LoadedArtifacts:
        if self._cache is not None and not force_reload:
            return self._cache

        drc = self._load_yaml(self.drc_file)
        sb = self._load_yaml(self.sb_file)
        dr = self._load_yaml(self.dr_file)
        rb = self._load_yaml(self.rb_file)

        artifacts: Dict[str, Dict[str, Any]] = {}
        for artifact in (sb, dr, rb):
            artifact_id = artifact.get("id")
            if not isinstance(artifact_id, str) or not artifact_id:
                raise ValueError("Artifact missing valid 'id'.")
            artifacts[artifact_id] = artifact

        self._validate_drc_references(drc, artifacts)

        self._cache = LoadedArtifacts(drc=drc, artifacts=artifacts)
        return self._cache

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        file_path = self.artifact_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing artifact file: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            content = yaml.safe_load(file)

        if not isinstance(content, dict):
            raise ValueError(f"Artifact file does not contain a YAML object: {file_path}")

        return content

    @staticmethod
    def _validate_drc_references(
        drc: Dict[str, Any], artifacts: Dict[str, Dict[str, Any]]
    ) -> None:
        refs = drc.get("refs")
        if not isinstance(refs, dict):
            raise ValueError("DRC must contain 'refs' object.")

        for group in ("sb", "dr", "rb"):
            ids = refs.get(group)
            if not isinstance(ids, list):
                raise ValueError(f"DRC refs '{group}' must be a list.")
            for artifact_id in ids:
                if artifact_id not in artifacts:
                    raise ValueError(f"DRC ref '{artifact_id}' not found in loaded artifacts.")
