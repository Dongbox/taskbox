import sys
import time
from typing import Any, Dict
from enum import Enum

from taskbox.thread import StoppableThread
from taskbox.exceptions import FunctionTimedOut


class ExceptionType(Enum):
    TIMEOUT = 1
    EXCEPTION = 2


class Task:
    def __init__(self, timeout: float = 3) -> None:
        self.__timeout = timeout

        self.__main_thread = None
        self.__exception = None
        self.__ret = None
        self.__is_stopped = False
        self.__exception_type = None
        # shared between Multi Task
        self._shared_data: Dict = None

    def run(self):
        """
        子类应该实现这个方法来定义具体的进程任务逻辑
        """
        raise NotImplementedError

    def start(self) -> None:
        # 执行函数
        def funcwrap():
            try:
                self.__ret = self.run()
            except FunctionTimedOut:
                # Don't print traceback to stderr if we time out
                self.__is_stopped = True
                self.__exception_type = ExceptionType.TIMEOUT

            except Exception as e:
                self.__is_stopped = True
                self.__exception_type = ExceptionType.EXCEPTION

                exc_info = sys.exc_info()
                e.__traceback__ = exc_info[2].tb_next
                self.__exception = e

        self.__main_thread = StoppableThread(target=funcwrap)
        self.__main_thread.daemon = True

        self.__main_thread.start()
        self.__main_thread.join(self.__timeout)

    def terminate(self) -> Any:
        if self.__main_thread is None:
            raise ValueError("Thread is not started")
        func = self.run
        timeout = self.__timeout

        if self.__main_thread.is_alive():
            if self.__exception_type == ExceptionType.TIMEOUT:

                class FunctionTimedOutTempType(FunctionTimedOut):
                    def __init__(self):
                        return FunctionTimedOut.__init__(self, "", timeout, func)

                FunctionTimedOutException = type(
                    "FunctionTimedOut" + str(hash("%d_%d" % (id(timeout), id(func)))),
                    FunctionTimedOutTempType.__bases__,
                    dict(FunctionTimedOutTempType.__dict__),
                )

                stopException = FunctionTimedOutException
            else:
                stopException = self.__exception.__class__
            self.__main_thread._stopThread(stopException)
            self.__main_thread.join(min(0.1, timeout / 50.0))

            raise FunctionTimedOut("", timeout, func)
        else:
            # We can still cleanup the thread here..
            # Still give a timeout... just... cuz..
            self.__main_thread.join(0.5)

        if self.__exception is not None:
            raise self.__exception from None

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
