# Copyright (c) 2016, 2017, 2019 Timothy Savannah All Rights Reserved.
#
# Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have received a copy of this with the source distribution as
# LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
#
# Copyright (c) 2023, 2024 Dongbo Xie All Rights Reserved.
#
# Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
# LICENSE, otherwise it is available at <https://github.com/Dongbox/taskbox/LICENSE>.

import os
import ctypes
import threading
from typing import Any, Callable, Optional, Sequence
from multiprocessing.synchronize import Event
from datetime import datetime
import traceback

from .shared import SharedData
from .data import Unpack, Data
from .base import TerminatedData

class Task:
    """
    The Task class is used to create and manage tasks with TimeoutError.

    Raises:
        NotImplementedError: If the `run` method is not implemented by the subclass.
        ValueError: If the task is not started before calling other methods.
        TimeoutError: If the task exceeds the specified timeout.
    """

    _instantiated = False

    def __init__(
        self, timeout: Optional[float] = None, *, execute_requires: Sequence = []
    ) -> None:
        """
        Initializes a new instance of the Task class.
        """
        self._ret = None
        self._timeout = timeout

        # shared between All Task
        self.shared: SharedData = None

        # terminate event for taskbox
        self._terminate_data: TerminatedData = None

        # instantiated flag
        self._instantiated = True

        # Thread About
        self.__main_thread = None
        self.__start_date = None

        # Function Arguments Initialization
        self._execute_requires = execute_requires
        self._callback_func = None
        self._error_callback_func = None

        # Auto-generated ident
        self.ident = self._generate_ident()

    @property
    def result(self) -> Any:
        return self._ret

    @property
    def timeout(self) -> float:
        return self._timeout

    def set_terminate_event(self, terminate_data: TerminatedData) -> None:
        """
        Sets the terminate data for the task.

        Args:
            terminate_data (TerminatedData): The terminate data object.
        """
        self._terminate_data = terminate_data

    def set_callback_func(self, callback_func: Callable) -> None:
        if not isinstance(callback_func, Callable):
            raise ValueError(f"[{self.__class__.__name__}]: `callback_func` must be a callable function")
        
        self._callback_func = callback_func

    def set_shared_data(self, shared_data: SharedData) -> None:
        """
        Sets the shared data for the task.

        Args:
            shared_data (SharedData): The shared data object.
        """
        self.shared = shared_data

    def set_timeout(self, timeout: float) -> None:
        """
        Sets the timeout for the task.

        Args:
            timeout (float): The timeout in seconds.
        """
        self._timeout = timeout

    def set_execute_requires(self, *execute_requires) -> None:
        """
        Sets the function arguments for the task.

        Args:
            execute_requires (Any): The function arguments.
        """
        self._execute_requires = execute_requires

    def parse_execute_requires(self) -> Sequence:
        """
        Parses the function arguments for the task.

        When Collection exists in the arguments, it will be replaced with the actual value.
        """
        execute_requires = []
        for arg in self._execute_requires:
            if isinstance(arg, Unpack):
                for data in arg:
                    execute_requires.append(data)
            elif isinstance(arg, Data):
                execute_requires.append(arg.value)
            else:
                execute_requires.append(arg)
                
        return execute_requires

    def execute(self, *required: Sequence) -> Any:
        """
        This method should be implemented by the subclass to define the specific task logic.
        """
        raise NotImplementedError

    def _terminate(self, exception: Optional[BaseException] = None) -> Any:
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
                err_msg = traceback.format_exc()
            else:
                # Timeout if the thread is still alive
                exception = TimeoutError
                err_msg = f"TimeoutError: {self._timeout} seconds timeout exceeded"

            # Set the terminate event that other tasks can listen to (With Taskbox)
            if self._terminate_data is not None:
                self._terminate_data.set_event()
                self._terminate_data.set_err_msg(err_msg)
            self.__main_thread.stop()

            self._error_callback_func(exception)
            raise exception

    def start(
        self,
        timeout: Optional[float] = None,
        wait: bool = True,
        callback_func: Optional[Callable] = None,
        error_callback_func: Optional[Callable] = None,
    ) -> Any:
        """
        Starts the task.

        Args:
            wait (bool, optional): Whether to wait for the task to finish. Defaults to True.
            callback_func (Callable, optional): The callback function to be called after the task finishes. Defaults to None.

        Returns:
            Any: None if the `callback` function is set, otherwise the return value of the `run` method.
        """
        # parse execute required
        execute_requires = self.parse_execute_requires()
        
        self._error_callback_func = error_callback_func

        # update timeout if set
        if timeout is not None:
            self.set_timeout(timeout)

        def funcwrap():
            try:
                self._ret = self.execute(*execute_requires)

                # callback
                if callback_func is not None:
                    callback_func(self._ret)
                
            except BaseException as e:
                # Error handling
                self._terminate(e)

        self.__main_thread = StoppableThread(target=funcwrap)
        self.__main_thread.daemon = True

        self.__main_thread.start()
        self.__start_date = datetime.now()

        # Wait for the main thread to finish
        if wait:
            self.__main_thread.join(self._timeout)
            # check
            self._terminate()
            return self._ret
        else:
            # Set the start date and use in the join method
            self.__start_date = datetime.now()
            return None

    def wait(self) -> None:
        """
        Wait for the main thread to finish.
        """
        if self.__main_thread is None:
            raise ValueError("Task not started")

        # Check if start date is set
        if self.__start_date is None:
            return

        # Calculate remaining timeout if timeout is set
        if self._timeout is not None:
            remaining_timeout = (
                self._timeout - (datetime.now() - self.__start_date).total_seconds()
            )
            if remaining_timeout < 0:
                # Timeout error
                self._terminate(TimeoutError)
            else:
                self.__main_thread.join(remaining_timeout)
        else:
            # No timeout, simply join the main thread
            self.__main_thread.join()

        # Check if the main thread is still alive after joining
        if self.__main_thread.is_alive():
            # Timeout error
            self._terminate(TimeoutError)
        else:
            # Terminate the task
            self._terminate()

    def _generate_ident(self) -> str:
        """
        Generates an auto-generated ident for the task.

        Returns:
            str: The auto-generated ident.
        """
        return f"Task_{id(self)}"


class StoppableThread(threading.Thread):
    """
    StoppableThread - A thread that can be stopped by forcing an exception in the execution context.

      This works both to interrupt code that is in C or in python code, at either the next call to a python function,
       or the next line in python code.

    It is recommended that if you call stop ( @see StoppableThread.stop ) that you use an exception that inherits BaseException, to ensure it likely isn't caught.

     Also, beware unmarked exception handlers in your code. Code like this:

        while True:
            try:
                doSomething()
            except:
                continue

    will never be able to abort, because the exception you raise is immediately caught.

    The exception is raised over and over, with a specifed delay (default 2.0 seconds)
    """

    def _stopThread(self, raise_every: float):
        """
        _stopThread - @see StoppableThread.stop
        """
        if self.is_alive() is False:
            return True

        self._stderr = open(os.devnull, "w")

        # Create "joining" thread which will raise the provided exception
        #  on a repeat, until the thread stops.
        join_thread = JoinThread(self, repeat_every=raise_every)

        # Try to prevent spurrious prints
        join_thread._stderr = self._stderr
        join_thread.start()
        join_thread._stderr = self._stderr
        join_thread.join(0.5)

    def stop(self, raise_every=2.0):
        """
        Stops the thread by raising a given exception.

        @param exception <Exception type> - Exception to throw. Likely, you want to use something

          that inherits from BaseException (so except Exception as e: continue; isn't a problem)

          This should be a class/type, NOT an instance, i.e.  MyExceptionType   not  MyExceptionType()


        @param raiseEvery <float> Default 2.0 - We will keep raising this exception every #raiseEvery seconds,

            until the thread terminates.

            If your code traps a specific exception type, this will allow you #raiseEvery seconds to cleanup before exit.

            If you're calling third-party code you can't control, which catches BaseException, set this to a low number

              to break out of their exception handler.


         @return <None>
        """
        return self._stopThread(raise_every)


class JoinThread(threading.Thread):
    """
    JoinThread - The workhouse that stops the StoppableThread.

        Takes an exception, and upon being started immediately raises that exception in the current context
          of the thread's execution (so next line of python gets it, or next call to a python api function in C code ).

        @see StoppableThread for more details
    """

    def __init__(self, other_thread: threading.Thread, repeat_every: float):
        """
        __init__ - Create a JoinThread (don't forget to call .start() ! )

            @param otherThread <threading.Thread> - A thread

            @param exception <BaseException> - An exception. Should be a BaseException, to prevent "catch Exception as e: continue" type code
              from never being terminated. If such code is unavoidable, you can try setting #repeatEvery to a very low number, like .00001,
              and it will hopefully raise within the context of the catch, and be able to break free.

            @param repeatEvery <float> Default 2.0 - After starting, the given exception is immediately raised. Then, every #repeatEvery seconds,
              it is raised again, until the thread terminates.
        """
        threading.Thread.__init__(self)
        self.other_thread = other_thread
        self.repeat_every = repeat_every
        self.daemon = True

    def run(self):
        """
        run - The thread main. Will attempt to stop and join the attached thread.
        """
        # Try to silence default exception printing.
        self.other_thread._Thread__stderr = self._stderr

        while self.other_thread.is_alive():
            # We loop raising exception incase it's caught hopefully this breaks us far out.
            self._async_raise(self.other_thread.ident)
            self.other_thread.join(self.repeat_every)
        try:
            self._stderr.close()
        except:
            pass

    @staticmethod
    def _async_raise(tid: int):
        """raises the exception, performs cleanup if needed"""
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
