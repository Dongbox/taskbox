import time
from typing import Any, Dict, Callable, Tuple
from multiprocessing import Event

from taskbox.thread import StoppableThread


class Task:
    _instantiated = False

    def __init__(self) -> None:
        self.__main_thread = None
        self.__ret = None
        self.__callback = None
        self.__timeout = None

        # shared between Multi Task
        self._shared_data: Dict = None
        self._terminate_event: Event = None

        # instantiated flag
        self._instantiated = True

    def set_timeout(self, timeout: int) -> None:
        self.__timeout = timeout

    def set_func_args(self, args: Tuple = None, kwargs: Dict = None) -> None:
        """
        设置函数参数

        Args:
            args: 位置参数
            kwargs: 关键字参数

        """
        self._args = args
        self._kwargs = kwargs

    def set_callback(self, callback: Callable) -> None:
        """
        Set the callback function

        The callback function will be called after the task is completed,
        but if the task is terminated, the callback function will not be called.

        Args:
            callback: The callback function

        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self.__callback = callback

    def run(self, *args, **kwargs):
        """
        子类应该实现这个方法来定义具体的进程任务逻辑
        """
        raise NotImplementedError

    def start(self) -> Any:
        """
        Start the task

        Returns:
            Any: None if the `callback` function is set, otherwise the return value of the `run` method
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

        # Call the callback function
        if self.__callback is not None:
            self.__callback(self.__ret)
            return None
        else:
            return self.__ret

    def terminate(self, exception: BaseException = None) -> Any:
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
            self.__main_thread.join(wait_time)

    # --------------- TaskBox Shared Data ---------------
    def _get_shared_data(self) -> Dict:
        if self._shared_data is None:
            raise ValueError("Shared data not set")
        return self._shared_data

    def get_data(self, name: str):
        shared_data = self._get_shared_data()
        while True:
            result = shared_data.get(name)
            if result is not None:
                return result
            time.sleep(0.1)

    def set_data(self, name: str, value: Any):
        shared_data = self._get_shared_data()
        shared_data[name] = value
        self._shared_data = shared_data
