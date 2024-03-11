# -*- coding: utf-8 -*-
"""
File: box.py
Author: Dongbox
Date: 2024-03-11
Description:
This module provides a class for managing tasks and executing them in parallel or Series mode.

"""
from typing import Tuple, Dict, List, Callable, NamedTuple
from multiprocessing import Manager
from multiprocessing.pool import Pool, AsyncResult
from enum import Enum
from .task import Task
from .exceptions import ParamsError
from .shared_data import SeriesSharedDict, ParallelSharedDict


class CandidatedTask(NamedTuple):
    task: Task
    args: tuple
    kwargs: dict
    callback: Callable


class Mode(Enum):
    PARALLEL = "parallel"
    SERIES = "series"


class TaskBox:
    def __init__(
        self, mode: Mode = Mode.PARALLEL, max_workers: int = 4, timeout: float = None
    ) -> None:
        """
        Initialize a TaskBox object.

        Args:
            parallel (bool, optional): Whether to run tasks in parallel. Defaults to True.
            max_workers (int, optional): The maximum number of worker processes. Defaults to 4.
            timeout (float, optional): The timeout duration for each task. Defaults to None.
        """
        self._mode = mode

        # Process tasks
        self._tasks: List[CandidatedTask] = []

        # Timeout duration for child process tasks
        self.timeout = timeout

        # Callback function
        self._callback = None

        if self._mode == Mode.PARALLEL:
            # Create a process pool
            self._pool = Pool(processes=max_workers)

            # Save all current tasks in the process pool (including completed tasks if not cleared)
            self._results: List[AsyncResult] = []

            # Process manager for creating shared objects and signals between processes
            self._manager = Manager()

            # Global shared data
            self.shared_data = ParallelSharedDict(self._manager)
            self.terminate_event = self._manager.Event()
        else:
            self.shared_data = SeriesSharedDict()
            self.terminate_event = None

    def add_callback_func(self, callback: Callable) -> None:
        """
        Add a callback function to be executed after each task completes.

        Args:
            callback (Callable): The callback function to be added.
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self._callback = callback

    def error_callback(self, async_result: AsyncResult) -> None:
        """
        Error callback function to handle any errors that occur during task execution.

        Args:
            async_result (AsyncResult): The asynchronous result object.
        """
        print(async_result)

    def start(self):
        """
        Start executing the tasks in the TaskBox.
        """
        if self._mode == Mode.PARALLEL:
            self._parallel_start()
        else:
            self._series_start()

    def _parallel_start(self):

        # Default use global callback function
        callback_func = self._callback

        # Loop through all tasks
        for candidated_task in self._tasks:
            task = candidated_task.task
            # Set global shared data and terminate event
            task.shared_data = self.shared_data
            task._terminate_event = self.terminate_event

            # Set timeout
            if self.timeout is not None:
                task.set_timeout(self.timeout)

            # Set params
            task.set_func_args(candidated_task.args, candidated_task.kwargs)

            # If callback is set, submit task to pool with callback (Process AsyncResult object in callback function)
            if candidated_task.callback is not None:
                callback_func = candidated_task.callback

            # Submit task to pool
            async_result = self._pool.apply_async(
                task.start, callback=callback_func, error_callback=self.error_callback
            )

            # Add async_result to global list
            self._results.append(async_result)

        # Clear finished tasks
        self._tasks.clear()

    def _series_start(self):
        """
        Start executing the tasks in the TaskBox.
        """
        # Loop through all tasks
        for candidated_task in self._tasks:
            task = candidated_task.task
            # Set global shared data and terminate event
            task.shared_data = self.shared_data
            task._terminate_event = self.terminate_event

            # Set timeout
            if self.timeout is not None:
                task.set_timeout(self.timeout)

            # Set params
            task.set_func_args(candidated_task.args, candidated_task.kwargs)

            # Start task
            ret = task.start()

            # If callback is set, execute callback function
            if candidated_task.callback is not None:
                candidated_task.callback(ret)

        # Clear finished tasks
        self._tasks.clear()

    def submit_task(
        self,
        task: Task,
        args: Tuple = (),
        kwargs: Dict = {},
        callback_func: Callable = None,
    ):
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

        # If args has only one element, ensure it is a tuple (with a comma)
        if not isinstance(args, tuple):
            raise ParamsError(
                "`args` must be a tuple, even if it only has one element. Tips: (1, )"
            )

        # If kwargs is empty, ensure it is a dict
        if not isinstance(kwargs, dict):
            raise ParamsError("`kwargs` must be a dict")

        # Add task to the task list
        self._tasks.append(CandidatedTask(task, args, kwargs, callback_func))

    def wait(self):
        """
        Block the main process until all tasks are completed.
        """
        if self._mode != Mode.PARALLEL:
            raise ValueError(
                "The `wait` method is only available in `Mode.PARALLEL` mode"
            )

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
