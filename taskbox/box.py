from typing import List, Callable, NamedTuple
from multiprocessing import Manager
from multiprocessing.pool import Pool, AsyncResult

from .task import Task


class TaskDefined(NamedTuple):
    task: Task
    callback: Callable
    args: tuple
    kwargs: dict


class TaskBox:
    def __init__(
        self, max_workers: int = 4, is_timer: bool = False, timeout: float = None
    ) -> None:
        # 创建一个进程池
        self._pool = Pool(processes=max_workers)

        # 保存当前进程池的所有任务（如果未清空则会包括已完成的任务）
        self._async_results: List[AsyncResult] = []

        # 进程管理器，用于创建进程间共享对象和信号
        self._manager = Manager()

        # 全局共享数据
        self.shared_data = self._manager.dict()
        self.terminate_event = self._manager.Event()

        # 进程任务
        self._tasks: List[TaskDefined] = []

        # 是否记录任务执行时间
        self.is_timer = is_timer

        # 子进程任务超时时长
        self.timeout = timeout

    def start(self):
        # 遍历声明的任务，实例化后，查询run方法是否存在，不存在则抛出异常
        for task_defined in self._tasks:
            task = task_defined.task
            # 设置共享数据和终止事件
            task._shared_data = self.shared_data
            task._terminate_event = self.terminate_event

            # Set timeout
            if self.timeout is not None:
                task.set_timeout(self.timeout)

            # Set params
            task.set_func_args(task_defined.args, task_defined.kwargs)

            # Submit task to pool
            async_result = self._pool.apply_async(
                task.start, callback=task_defined.callback
            )

            # Add async_result to global list
            self._async_results.append(async_result)

        # 清空任务列表
        self._tasks.clear()

    def submit_task(self, task: Task, callback_func: Callable, *args, **kwargs):
        """
        提交任务到进程池进行执行后添加到任务列表继续维护

        Args:
            func (Function):要执行的函数
            callback_func (Function): 回调函数
        """
        # 判断task是否为Task的子类
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task")

        # 判断task是否完成实例化
        if not hasattr(task, "_instantiated") or not task._instantiated:
            raise ValueError("task must be instantiated")

        # 添加任务到任务列表
        self._tasks.append(TaskDefined(task, callback_func, args, kwargs))

    def wait(self):
        """
        等待进程池中所有任务完成，并清空全局任务记录中的任务
        """
        # 等待所有futures执行完成
        while self._async_results:
            for async_result in self._async_results:
                if async_result.ready():
                    self._async_results.remove(async_result)

                # 如果终止事件被设置，则终止进程池
                if self.terminate_event.is_set():
                    self._pool.terminate()
                    self._pool.join()
                    return
