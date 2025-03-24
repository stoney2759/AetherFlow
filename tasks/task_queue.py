import queue
import logging

class TaskQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.logger = logging.getLogger("TaskQueue")

    def add_task(self, task: str):
        """Adds a task to the queue, ensuring it is a full string."""
        self.logger.debug(f"🔍 Raw Task Input: {repr(task)}")  # Debug log task input

        if isinstance(task, str) and len(task.strip()) > 1:
            self.queue.put(task.strip())  # ✅ Ensure full strings are added
        else:
            self.logger.warning(f"⚠️ Skipping invalid task (too short or empty): {repr(task)}")

    def get_task(self):
        """Retrieves a task from the queue."""
        if not self.queue.empty():
            return self.queue.get()
        return None

    def is_empty(self):
        """Checks if the queue is empty."""
        return self.queue.empty()

    def execute_all(self, worker_fn):
        """Executes all tasks in the queue using the provided worker function."""
        while not self.queue.empty():
            task = self.get_task()
            if task:
                self.logger.info(f"🚀 Executing Task: {task}")
                worker_fn(task)

