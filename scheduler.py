import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import SCAN_INTERVAL_HOURS

logger = logging.getLogger(__name__)

def start_scheduler(bot):
    scheduler = BackgroundScheduler()

    def run_scan():
        from scraper import scan_all_creators
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(scan_all_creators(bot))
        finally:
            loop.close()

    scheduler.add_job(
        run_scan,
        trigger=IntervalTrigger(hours=SCAN_INTERVAL_HOURS),
        id="scan_job",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"✅ Scheduler démarré — scan toutes les {SCAN_INTERVAL_HOURS}h")
