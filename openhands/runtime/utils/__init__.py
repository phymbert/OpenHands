from __future__ import annotations

import os
from pathlib import Path

from openhands.runtime.utils.system import (  # noqa: F401
    display_number_matrix,
    find_available_tcp_port,
)

_DEFAULT_RUNTIME_ROOT = Path('/openhands')


def get_runtime_root() -> Path:
    override = os.environ.get('OPENHANDS_RUNTIME_ROOT')
    if override:
        try:
            return Path(override)
        except TypeError:  # pragma: no cover - defensive
            return _DEFAULT_RUNTIME_ROOT
    return _DEFAULT_RUNTIME_ROOT


def runtime_path(*parts: str) -> str:
    return str(get_runtime_root().joinpath(*parts))


def replace_runtime_root(value: str) -> str:
    default_root = str(_DEFAULT_RUNTIME_ROOT)
    runtime_root = str(get_runtime_root())
    if value.startswith(default_root):
        return runtime_root + value[len(default_root) :]
    return value.replace(default_root, runtime_root)


__all__ = [
    'display_number_matrix',
    'find_available_tcp_port',
    'get_runtime_root',
    'replace_runtime_root',
    'runtime_path',
]
