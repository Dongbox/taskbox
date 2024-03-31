# Copyright (c) 2023, 2024 Dongbo Xie All Rights Reserved.
#
# Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
# LICENSE, otherwise it is available at <https://github.com/Dongbox/taskbox/LICENSE>.


from typing import List, Callable, Any, Dict, Sequence
from functools import wraps
from multiprocessing import Manager
from multiprocessing.pool import Pool, ApplyResult
from .task import Task
from .shared import SharedData, SerialSharedDict, ParallelSharedDict


class TaskBox:
    def __init__(self) -> None:
        """
        Initialize a TaskBox object.

        Args:
            max_workers (int, optional): The maximum number of worker processes. Defaults to 4.
            timeout (float, optional): The timeout duration for each task. Defaults to None.
        """

        # Process tasks
        self._tasks: List[Task] = []
        self._shared_data: SharedData = None

    def add_task(self, task: Task):
        """
        Add a task to the TaskBox for execution.

        Args:
            task (Task): The task to be executed.
            args (Tuple, optional): Positional arguments for the task. Defaults to ().
            kwargs (Dict, optional): Keyword arguments for the task. Defaults to {}.
            callback_func (Callable, optional): The callback function to be executed after the task completes. Defaults to None.
        """
        # Check if task is a subclass of Task
        if not isinstance(task, Task):
            raise KeyError("`task` must be a subclass of Task")

        # Check if task is instantiated
        if not hasattr(task, "_instantiated") or not task._instantiated:
            raise KeyError("`task` must be instantiated")

        # Add task to the task list
        self._tasks.append(task)

    def add_tasks(self, task_dict: Dict[Task, Sequence]):
        """
        Add a dictionary of tasks to the TaskBox for execution.

        Args:
            task_dict (Dict[Task, Sequence]): A dictionary of tasks to be executed.
        """
        for task, data_list in task_dict.items():
            self.add_task(task(execute_requires=data_list))

    def start(self, timeout: float = None, callback_func: Callable = None):
        """
        Start executing the tasks in the TaskBox.
        """
        raise NotImplementedError

    def reset(self):
        """
        Reset the TaskBox by clearing all tasks and shared data.
        """
        self._tasks.clear()


# Wrap the callback function with the task object
def wrap_callback_with_task(task: Task, callback_func: Callable):
    @wraps(callback_func)
    def wrapper(result: Any):
        # 将结果保存到相应的 Task 对象中
        task._ret = result
        # 调用传入的回调函数进行处理
        callback_func(result)

    return wrapper


class ParallelTaskBox(TaskBox):
    def __init__(
        self,
        max_workers: int = 4,
    ) -> None:
        super().__init__()
        # Process manager for creating shared objects and signals between processes
        self._manager = Manager()

        # Global shared data
        self._shared_data = ParallelSharedDict(self._manager)

        # Create a process pool
        self._pool = Pool(processes=max_workers)

        # Save all current tasks in the process pool (including completed tasks if not cleared)
        self._results: List[ApplyResult] = []

        # Terminate event to signal the process pool to terminate
        self._terminate_event = self._manager.Event()

    def error_callback(self, async_result: Any) -> None:
        """
        Error callback function to handle any errors that occur during task execution.

        Args:
            async_result (ParallelResult): The asynchronous result object.
        """
        print(async_result)

    def start(self, timeout: float = None, callback_func: Callable = None):

        # Loop through all tasks
        for task in self._tasks:
            # Set global shared data and terminate event
            task.set_shared_data(self._shared_data)
            task.set_terminate_event(self._terminate_event)

            # Set timeout if not already set
            if timeout is not None and task.timeout is None:
                task.set_timeout(timeout)

            # Submit task to pool
            async_result = self._pool.apply_async(
                task.start,
                callback=(
                    wrap_callback_with_task(task, callback_func)
                    if callback_func is not None
                    else None
                ),
                error_callback=self.error_callback,
            )

            # Add async_result to global list
            self._results.append(async_result)

        return self

    def reset(self):
        super().reset()

        # Clear all results from the process pool
        self._shared_data = ParallelSharedDict(self._manager)
        self._terminate_event = self._manager.Event()
        self._results = []

    def wait(self):
        """
        Block the main process until all tasks are completed.
        """
        while self._results:
            completed_results = []
            for async_result in self._results:
                if async_result.ready():
                    completed_results.append(async_result)

            # Remove completed results from the global list
            self._results = [
                result for result in self._results if result not in completed_results
            ]

            # Terminate the process pool if the terminate event is set
            if self._terminate_event.is_set():
                self._pool.terminate()
                self._pool.join()
                return


class SerialTaskBox(TaskBox):
    def __init__(self) -> None:
        super().__init__()

        self._shared_data = SerialSharedDict()

    def start(self, timeout: float = None, callback_func: Callable = None):
        """
        Start executing the tasks in the TaskBox.
        """

        # Loop through all tasks
        for task in self._tasks:
            # Set global shared data and terminate event
            task.set_shared_data(self._shared_data)

            # Start task
            ret = task.start(timeout=timeout, wait=True)

            if callback_func is not None:
                callback_func(ret)

    def reset(self):
        super().reset()

        self._shared_data = SerialSharedDict()
