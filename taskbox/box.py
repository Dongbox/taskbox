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
from enum import Enum
from .task import Task
from .exceptions import ParamsError
from .shared_data import SeriesSharedDict, ParallelSharedDict


class Mode(Enum):
    PARALLEL = "parallel"
    SERIES = "series"


class TaskBox:
    def __init__(self, timeout: float = None) -> None:
        """
        Initialize a TaskBox object.

        Args:
            max_workers (int, optional): The maximum number of worker processes. Defaults to 4.
            timeout (float, optional): The timeout duration for each task. Defaults to None.
        """

        # Process tasks
        self._tasks: List[Task] = []

        # Timeout duration for child process tasks
        self.timeout = timeout

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

    def start(self, callback_func: Callable = None):
        """
        Start executing the tasks in the TaskBox.
        """
        raise NotImplementedError


class ParallelTaskBox(TaskBox):
    def __init__(self, timeout: float = None, max_workers: int = 4) -> None:
        super().__init__(timeout)

        # Create a process pool
        self._pool = Pool(processes=max_workers)

        # Save all current tasks in the process pool (including completed tasks if not cleared)
        self._results: List[AsyncResult] = []

        # Process manager for creating shared objects and signals between processes
        self._manager = Manager()

        # Global shared data
        self.shared_data = ParallelSharedDict(self._manager)
        self.terminate_event = self._manager.Event()

    def start(self, callback_func: Callable = None):

        # Loop through all tasks
        for task in self._tasks:
            # Set global shared data and terminate event
            task.shared_data = self.shared_data
            task._terminate_event = self.terminate_event

            # Set timeout if not already set
            if self.timeout is not None and task.timeout is None:
                task._timeout = self.timeout

            # Submit task to pool
            async_result = self._pool.apply_async(
                task.start, callback=callback_func, error_callback=self.error_callback
            )

            # Add async_result to global list
            self._results.append(async_result)

        # Clear finished tasks
        self._tasks.clear()

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
            if self.terminate_event.is_set():
                self._pool.terminate()
                self._pool.join()
                return


class SeriesTaskBox(TaskBox):
    def __init__(self, timeout: float = None) -> None:
        super().__init__(timeout)

        self.shared_data = SeriesSharedDict()
        self.terminate_event = None

    def start(self, callback_func: Callable = None):
        """
        Start executing the tasks in the TaskBox.
        """
        # Loop through all tasks
        for task in self._tasks:
            # Set global shared data and terminate event
            task.shared_data = self.shared_data
            task._terminate_event = self.terminate_event

            # Set timeout if not already set
            if self.timeout is not None and task.timeout is None:
                task._timeout = self.timeout

            # Start task
            ret = task.start(wait=False)

            if callback_func is not None:
                callback_func(ret)

        # Clear finished tasks
        self._tasks.clear()
