import logging
import asyncio
from src.app.scheduler_service import SchedulerService
from src.app.config.logging_config import setup_logging

def main() -> None:
    """
    Main function to run the application, including the scheduler.
    """
    setup_logging() # Configure logging first
    logger = logging.getLogger(__name__) # Get logger after configuration

    logger.info("Starting the Provida application...")
    
    scheduler_service = SchedulerService()
    scheduler_service.start()

    try:
        # Keep the main thread alive to allow scheduled jobs to run
        # In a real application, this might be part of a web server or other long-running process
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler_service.shutdown()
        logger.info("Provida application shut down.")

if __name__ == "__main__":
    main()
