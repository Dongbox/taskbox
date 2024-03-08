from typing import List, Callable, NamedTuple
from concurrent.futures import Future, ProcessPoolExecutor, wait
from multiprocessing import Manager
from functools import wraps
from exceptions import FunctionTimedOut

from task import Task


class TaskDefined(NamedTuple):
    task_class: Task
    callback: Callable
    args: tuple
    kwargs: dict


class TaskBox:
    def __init__(
        self, max_workers: int = 4, is_timer: bool = False, timeout: float = 3
    ) -> None:
        # 创建一个进程池
        self._pool = ProcessPoolExecutor(max_workers=max_workers)

        # 保存当前进程池的所有任务（如果未清空则会包括已完成的任务）
        self._futures: List[Future] = []

        # 进程管理器，用于创建进程间共享对象和信号
        self._manager = Manager()

        # 全局共享数据
        self.shared_data = self._manager.dict()

        # 进程任务
        self.defined_tasks: List[TaskDefined] = []

        # 是否记录任务执行时间
        self.is_timer = is_timer

        # 子进程任务超时时长
        self.timeout = timeout

    def start(self):
        if not self.defined_tasks:
            print("No task to start")
            return

        # 遍历声明的任务，实例化后，查询run方法是否存在，不存在则抛出异常
        for task_defined in self.defined_tasks:
            task_class = task_defined.task_class
            if not hasattr(task_class, "run"):
                raise NotImplementedError(f"Task {task_class} must have a run method")

            # 设置共享数据和终止事件
            task_instance: Task = task_class(*task_defined.args, **task_defined.kwargs)
            task_instance._shared_data = self.shared_data
            # 提交任务到进程池

            # package_func = partial(func_timeout, 5, task_instance.run)
            future = self._pool.submit(task_instance.start)
            # 添加到任务列表
            self._futures.append(future)

        # 遍历添加回调函数
        for index, task_defined in enumerate(self.defined_tasks):
            self._futures[index].add_done_callback(
                self.decorator_callback_catch_exeception(
                    task_defined.callback, self._futures
                )
            )

        # 清空任务列表
        self.defined_tasks.clear()

    @staticmethod
    def decorator_callback_catch_exeception(
        callback_func: Callable, futures: List[Future]
    ):
        # 作为一个装饰器封装callback函数，捕获其中的异常报错，取消所有的任务
        @wraps(callback_func)
        def wrapper(future: Future):
            try:
                # 调用result()方法会抛出异常
                future.result()
                return callback_func(future)
            except (Exception, FunctionTimedOut) as e:
                print(e)
                # 取消所有任务
                for future in futures:
                    future.cancel()

        return wrapper

    def submit_task(self, task: Task, callback_func: Callable, *args, **kwargs):
        """
        提交任务到进程池进行执行后添加到任务列表继续维护

        Args:
            func (Function):要执行的函数
            callback_func (Function): 回调函数
        """
        self.defined_tasks.append(TaskDefined(task, callback_func, args, kwargs))

    def wait_finished(self):
        """
        等待进程池中所有任务完成，并清空全局任务记录中的任务
        """
        # 等待所有futures执行完成
        wait(self._futures)
        # 清空任务列表
        self._futures.clear()
