"""Scheduler service interface."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SchedulerService:
    """Interface orchestrator for scheduling platform auto-sync background jobs."""

    @staticmethod
    def register_job(job_id: str, cron_expression: str, task_func: Any, *args: Any) -> None:
        """Register a new recurring background synchronization job."""
        logger.info(
            f"[Scheduler] Registered job '{job_id}' with trigger '{cron_expression}'"
        )

    @staticmethod
    def pause_job(job_id: str) -> None:
        """Pause a currently running synchronization schedule."""
        logger.info(f"[Scheduler] Paused job '{job_id}'")

    @staticmethod
    def resume_job(job_id: str) -> None:
        """Resume a suspended synchronization schedule."""
        logger.info(f"[Scheduler] Resumed job '{job_id}'")
