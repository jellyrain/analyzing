from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EngineBuildProject:
    """
    engine 项目的构建上下文。
    """

    project_dir: Path
    main_file_path: Path
    pyproject_file_path: Path
    config_dir_path: Path
    default_config_file_path: Path
    project_name: str
    build_name: str = "engine"
    external_dir_paths: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class EngineBuildResult:
    """
    engine 构建结果。
    """

    release_dir: Path
    executable_file_path: Path
    included_files: list[str]
    external_dirs: list[str]
    metadata: dict[str, Any]
