# -*- coding: utf-8 -*-
"""
File: box.py
Author: Dongbox
Date: 2024-03-11
Description:
This module provides classes for managing tasks and executing them in different modes.

"""
from typing import Tuple, Dict, List, Callable, NamedTuple
from multiprocessing import Manager
from multiprocessing.pool import Pool, AsyncResult
from .task import Task
from .exceptions import ParamsError
from .shared_data import SharedData, SeriesSharedDict, ParallelSharedDict


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

    def error_callback(self, async_result: AsyncResult) -> None:
        """
        Error callback function to handle any errors that occur during task execution.

        Args:
            async_result (AsyncResult): The asynchronous result object.
        """
        print(async_result)

    def submit_task(self, task: Task):
        """
        Submit a task to the TaskBox for execution.

        Args:
            task (Task): The task to be executed.
            args (Tuple, optional): Positional arguments for the task. Defaults to ().
            kwargs (Dict, optional): Keyword arguments for the task. Defaults to {}.
            callback_func (Callable, optional): The callback function to be executed after the task completes. Defaults to None.
        """
        # Check if task is a subclass of Task
        if not isinstance(task, Task):
            raise ParamsError("`task` must be a subclass of Task")

        # Check if task is instantiated
        if not hasattr(task, "_instantiated") or not task._instantiated:
            raise ParamsError("`task` must be instantiated")

        # Add task to the task list
        self._tasks.append(task)

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
        self._results: List[AsyncResult] = []

        # Terminate event to signal the process pool to terminate
        self._terminate_event = self._manager.Event()

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
                callback=callback_func,
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


class SeriesTaskBox(TaskBox):
    def __init__(self) -> None:
        super().__init__()

        self._shared_data = SeriesSharedDict()

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

        self._shared_data = SeriesSharedDict()
