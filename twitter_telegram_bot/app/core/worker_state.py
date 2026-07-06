from __future__ import annotations

from enum import StrEnum


class WorkerState(StrEnum):
    INACTIVE = "inactive"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
