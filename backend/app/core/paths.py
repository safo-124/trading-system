from __future__ import annotations

import sys

from app.core.config import PROJECT_ROOT


def ensure_project_root_on_path() -> None:
    project_root = str(PROJECT_ROOT)
    if project_root not in sys.path:
        sys.path.append(project_root)
