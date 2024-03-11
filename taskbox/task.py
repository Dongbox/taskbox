# -*- coding: utf-8 -*-
"""
File: task.py
Author: Dongbox
Date: 2024-03-11
Description:
This module defines the Task class, which is used to create and manage tasks in a multi-threaded environment.

"""

from typing import Any, Dict, Callable, Tuple
from multiprocessing.synchronize import Event

from taskbox.thread import StoppableThread

from .shared_data import SharedData


class Task:
    _instantiated = False

    def __init__(self) -> None:
        """
        Initializes a new instance of the Task class.
        """
        self.__main_thread = None
        self.__ret = None
        self.__callback = None
        self.__timeout = None

        # shared between Multi Task
        self.shared_data: SharedData = None
        self._terminate_event: Event = None

        # instantiated flag
        self._instantiated = True

    def set_timeout(self, timeout: float) -> None:
        """
        Sets the timeout for the task.

        Args:
            timeout (float): The timeout value in seconds.
        """
        self.__timeout = timeout

    def set_func_args(self, args: Tuple = (), kwargs: Dict = {}) -> None:
        """
        Sets the function arguments for the task.

        Args:
            args (Tuple, optional): The positional arguments for the function. Defaults to ().
            kwargs (Dict, optional): The keyword arguments for the function. Defaults to {}.
        """
        self._args = args
        self._kwargs = kwargs

    def run(self, *args, **kwargs):
        """
        This method should be implemented by the subclass to define the specific task logic.
        """
        raise NotImplementedError

    def start(self) -> Any:
        """
        Starts the task.

        Returns:
            Any: None if the `callback` function is set, otherwise the return value of the `run` method.
        """

        def funcwrap():
            try:
                self.__ret = self.run(*self._args, **self._kwargs)
            except BaseException as e:
                # Error handling
                self.terminate(e)

        self.__main_thread = StoppableThread(target=funcwrap)
        self.__main_thread.daemon = True

        self.__main_thread.start()
        self.__main_thread.join(self.__timeout)

        # check
        self.terminate()

        return self.__ret

    def terminate(self, exception: BaseException = None) -> Any:
        """
        Terminates the task.

        Args:
            exception (BaseException, optional): The exception to be raised. Defaults to None.

        Returns:
            Any: The return value of the task.
        """
        if self.__main_thread is None:
            raise ValueError("Task not started")

        # Stop the main thread when an exception is raised or the timeout is exceeded
        if exception is not None or self.__main_thread.is_alive():
            wait_time = 0.5
            if exception is not None:
                import traceback

                print(traceback.format_exc())
            else:
                # Timeout if the thread is still alive
                exception = TimeoutError
                wait_time = min(0.1, self.__timeout / 50.0)
                print(f"TimeoutError: {self.__timeout} seconds timeout exceeded")

            # Set the terminate event that other tasks can listen to (With Taskbox)
            if self._terminate_event is not None:
                self._terminate_event.set()
            # Stop the main thread
            self.__main_thread.stop()
            # Wait for the join thread to finish
            # self.__main_thread.join(wait_time)
