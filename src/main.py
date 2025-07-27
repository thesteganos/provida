import logging
from src.app.scheduler import run_scheduler

# Setup logging
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main() -> None:
    """
    Main function to run the scheduler.
    """
    logging.info("Starting the scheduler...")
    # Run the scheduler to execute scheduled tasks
    run_scheduler()
    logging.info("Scheduler finished.")

if __name__ == "__main__":
    main()
