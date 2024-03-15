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
from datetime import datetime
import traceback
from .thread import StoppableThread
from .shared_data import SharedData


class Task:
    """
    The Task class is used to create and manage tasks with TimeoutError.

    Raises:
        NotImplementedError: If the `run` method is not implemented by the subclass.
        ValueError: If the task is not started before calling other methods.
        TimeoutError: If the task exceeds the specified timeout.

    Returns:
        Any: The return value of the task.
    """

    _instantiated = False

    def __init__(self, timeout: int = None) -> None:
        """
        Initializes a new instance of the Task class.
        """
        self._ret = None
        self.timeout = timeout

        # shared between Multi Task
        self.shared_data: SharedData = None
        self._terminate_event: Event = None

        # instantiated flag
        self._instantiated = True

        # Thread About
        self.__main_thread = None
        self.__start_date = None

        # Function Arguments Initialization
        self._args = ()
        self._kwargs = {}

    @property
    def result(self) -> Any:
        return self._ret

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

    def _terminate(self, exception: BaseException = None) -> Any:
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
            if exception is not None:
                print(traceback.format_exc())
            else:
                # Timeout if the thread is still alive
                exception = TimeoutError
                print(f"TimeoutError: {self.timeout} seconds timeout exceeded")
    
            # Set the terminate event that other tasks can listen to (With Taskbox)
            if self._terminate_event is not None:
                self._terminate_event.set()
            self.__main_thread.stop()

            raise exception
        
    def start(self, wait=True, callback_func: Callable = None) -> Any:
        """
        Starts the task.

        Args:
            wait (bool, optional): Whether to wait for the task to finish. Defaults to True.
            callback_func (Callable, optional): The callback function to be called after the task finishes. Defaults to None.

        Returns:
            Any: None if the `callback` function is set, otherwise the return value of the `run` method.
        """
        if callback_func is not None and wait is True:
            raise ValueError("callback_func cannot be used with wait=True")

        if callback_func is not None and not callable(callback_func):
            raise ValueError("callback_func must be callable")

        def funcwrap():
            try:
                self._ret = self.run(*self._args, **self._kwargs)

                # callback
                if callback_func is not None:
                    callback_func(self._ret)
            except BaseException as e:
                # Error handling
                self._terminate(e)

        self.__main_thread = StoppableThread(target=funcwrap)
        self.__main_thread.daemon = True

        self.__main_thread.start()

        # Wait for the main thread to finish
        if wait:
            self.__main_thread.join(self.timeout)
            # check
            self._terminate()
            return self._ret
        else:
            # Set the start date and use in the join method
            self.__start_date = datetime.now()
            return None

    def join(self) -> None:
        """
        Wait for the main thread to finish.
        """
        if self.__main_thread is None:
            raise ValueError("Task not started")

        # Check if start date is set
        if self.__start_date is not None:
            # Calculate remaining timeout if timeout is set
            if self.timeout is not None:
                remaining_timeout = (
                    self.timeout - (datetime.now() - self.__start_date).total_seconds()
                )
                if remaining_timeout < 0:
                    # Timeout error
                    self._terminate(TimeoutError)
                else:
                    self.__main_thread.join(remaining_timeout)
            else:
                # No timeout, simply join the main thread
                self.__main_thread.join()
        else:
            # Start date not set, return None
            return None

        # Check if the main thread is still alive after joining
        if self.__main_thread.is_alive():
            # Timeout error
            self._terminate(TimeoutError)
        else:
            # Terminate the task
            self._terminate()
