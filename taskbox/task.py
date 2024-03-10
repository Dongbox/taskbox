import sys
import time
from typing import Any, Dict
from enum import Enum

from taskbox.thread import StoppableThread
from taskbox.exceptions import FunctionTimedOut


class Task:
    def __init__(self) -> None:
        self.__timeout = None
        self.__main_thread = None
        self._exception = None
        self.__ret = None
        # shared between Multi Task
        self._shared_data: Dict = None

    def set_timeout(self, timeout: int) -> None:

        self.__timeout = timeout

    def set_func_args(self, *args, **kwargs) -> None:
        """
        设置函数参数

        Args:
            args: 位置参数
            kwargs: 关键字参数

        """
        self.__args = args
        self.__kwargs = kwargs

    def run(self, *args, **kwargs):
        """
        子类应该实现这个方法来定义具体的进程任务逻辑
        """
        raise NotImplementedError

    def start(self) -> None:
        # 执行函数
        def funcwrap():
            try:
                self.__ret = self.run(*self.__args, **self.__kwargs)
            except BaseException as e:
                # Error handling
                # exc_info = sys.exc_info()
                # e.__traceback__ = exc_info[2].tb_next
                self.terminate(e)

        self.__main_thread = StoppableThread(target=funcwrap)
        self.__main_thread.daemon = True

        self.__main_thread.start()
        self.__main_thread.join(self.__timeout)

        # Timeout if the thread is still alive
        if self.__main_thread.is_alive():
            self.terminate(TimeoutError)

    def _set_exception(self, exception: BaseException) -> None:
        """
        _set_exception_ - Set the exception and stop the thread

        Args:
            e (Exception): Exception to set
        """
        self._exception = exception
        self.__main_thread.stop()

    def terminate(self, exception: BaseException = None) -> Any:
        if self.__main_thread is None:
            raise ValueError("Task not started")

        if exception is not None:
            self._set_exception(exception)
            import traceback

            print(traceback.format_exc())
            raise self._exception

        if self.__main_thread.is_alive():
            # We need to stop the thread and raise an exception
            self.__main_thread.join(min(0.1, self.__timeout / 50.0))
        else:
            # We can still cleanup the thread here..
            # Still give a timeout... just... cuz..
            self.__main_thread.join(0.5)

        # if self._exception is not None:
        # raise self._exception from None

        if self.__ret is not None:
            return self.__ret

    def get_data(self, name: str):
        while True:
            result = self._shared_data.get(name)
            if result is not None:
                return result
            time.sleep(0.1)

    def set_data(self, name: str, value: Any):
        self._shared_data[name] = value
