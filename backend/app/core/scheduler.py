import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.session import async_session_maker

logger = logging.getLogger(__name__)


async def reset_nightly_baselines():
    """
    CRON job executing at midnight to recompute behavioral baselines
    from transaction history and reset daily velocity trackers.
    """
    logger.info("Executing Nightly Baseline Recomputation...")
    try:
        from app.services.baseline_service import update_all_baselines
        async with async_session_maker() as session:
            updated = await update_all_baselines(session)
            logger.info(f"Nightly Baseline Recomputation complete: {updated} users updated.")
    except Exception as e:
        logger.error(f"Failed to execute nightly baseline reset: {str(e)}")


def init_scheduler() -> AsyncIOScheduler:
    """Instantiate and attach jobs to the event loop scheduler."""
    scheduler = AsyncIOScheduler()

    # Run every midnight — recompute all user baselines from history
    scheduler.add_job(
        reset_nightly_baselines,
        trigger=CronTrigger(hour=0, minute=0),
        id="nightly_baseline_reset",
        name="Recompute User Behavioral Baselines",
        replace_existing=True
    )

    return scheduler
