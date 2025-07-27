import logging
from typing import Callable, List

# Setup logging
logging.basicConfig(filename='orchestrator.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Task:
    def __init__(self, name: str, action: Callable) -> None:
        """
        Initialize a Task.

        Args:
            name (str): The name of the task.
            action (Callable): The function to execute when the task runs.
        """
        self.name = name
        self.action = action

class Orchestrator:
    def __init__(self) -> None:
        """
        Initialize the Orchestrator.
        """
        logging.info("Orchestrator initialized.")
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """
        Add a task to the orchestrator.

        Args:
            task (Task): The task to add.
        """
        self.tasks.append(task)
        logging.info(f"Task '{task.name}' added.")

    def run(self) -> None:
        """
        Main method to run the orchestrator.
        """
        logging.info("Starting orchestrator...")
        for task in self.tasks:
            logging.info(f"Running task: {task.name}")
            task.action()
            logging.info(f"Task '{task.name}' completed.")
        logging.info("Orchestrator finished.")

if __name__ == "__main__":
    from src.app.scheduler import run_scheduler
    orchestrator = Orchestrator()
    orchestrator.add_task(Task("Run Scheduler", run_scheduler))
    orchestrator.run()