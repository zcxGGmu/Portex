"""Compatibility wrapper for the M7.2 execution coordinator."""

from services.execution_coordinator import ExecutionCoordinator


GroupQueueService = ExecutionCoordinator


__all__ = ["GroupQueueService"]
