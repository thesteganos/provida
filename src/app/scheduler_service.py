"""Utility for scheduling autonomous maintenance tasks."""

import logging
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from app.config.settings import settings
from app.agents.knowledge_curation_agent import KnowledgeCurationAgent

logger = logging.getLogger(__name__)

class SchedulerService:
    """Manage background jobs for knowledge curation.

    The service wraps an ``AsyncIOScheduler`` instance and exposes helper
    methods to register or remove jobs. Jobs are only added if automation is
    enabled in ``settings.automation``.
    """

    def __init__(self):
        self.jobstores = {
            'default': MemoryJobStore()
        }
        self.scheduler = AsyncIOScheduler(jobstores=self.jobstores)
        self.curation_agent = KnowledgeCurationAgent()
        logger.info("SchedulerService initialized.")

    def start(self):
        """
        Inicia o agendador e adiciona as tarefas iniciais.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")
            self._add_initial_jobs()
        else:
            logger.warning("Scheduler is already running.")

    def shutdown(self):
        """
        Desliga o agendador.
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down.")
        else:
            logger.warning("Scheduler is not running.")

    def _add_initial_jobs(self):
        """
        Adiciona as tarefas agendadas iniciais com base nas configurações.
        """
        if settings.automation.enabled:
            # Daily Knowledge Update
            daily_cron = settings.automation.daily_update_cron # e.g., "0 5 * * *" for 5 AM daily
            self.scheduler.add_job(
                self.curation_agent.perform_daily_update,
                CronTrigger.from_crontab(daily_cron),
                id='daily_knowledge_update',
                name='Atualização Diária do Conhecimento',
                replace_existing=True
            )
            logger.info(f"Scheduled daily knowledge update at {daily_cron}.")

            # Quarterly Review (example, needs more specific trigger)
            # For simplicity, let's say first day of Jan, Apr, Jul, Oct at 6 AM
            quarterly_cron = settings.automation.quarterly_review_cron # e.g., "0 6 1 */3 *"
            self.scheduler.add_job(
                self.curation_agent.perform_quarterly_review,
                CronTrigger.from_crontab(quarterly_cron),
                id='quarterly_review',
                name='Revisão Trimestral de Conflitos',
                replace_existing=True
            )
            logger.info(f"Scheduled quarterly review at {quarterly_cron}.")
        else:
            logger.info("Automation is disabled in settings. No jobs scheduled.")

    def add_job(
        self,
        func: Callable[..., Any],
        trigger: CronTrigger,
        id: str,
        name: str,
        **kwargs: Any,
    ) -> None:
        """Register a custom job with the scheduler.

        Parameters
        ----------
        func : Callable
            Coroutine or regular function to execute.
        trigger : CronTrigger
            Trigger defining when the job should run.
        id : str
            Unique identifier for the job.
        name : str
            Human friendly job name used in logs.
        **kwargs : Any
            Additional parameters forwarded to ``add_job``.
        """
        self.scheduler.add_job(func, trigger, id=id, name=name, **kwargs)
        logger.info("Job '%s' added to scheduler.", name)

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler by its identifier."""
        self.scheduler.remove_job(job_id)
        logger.info("Job '%s' removed from scheduler.", job_id)

# Example usage (for testing purposes, not part of the main application flow)
async def main():
    # This part would typically be managed by the main application entry point
    # and not run directly like this in a production setup.
    logging.basicConfig(level=logging.INFO)
    scheduler_service = SchedulerService()
    scheduler_service.start()

    try:
        # Keep the main thread alive to allow scheduled jobs to run
        while True:
            await asyncio.sleep(3600) # Sleep for an hour
    except (KeyboardInterrupt, SystemExit):
        scheduler_service.shutdown()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
