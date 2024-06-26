# TaskBox

## 简介

TaskBox是一个基于标准库实现的轻量级任务调度框架。它提供了一种简单而高效的方式来处理任务之间的数据依赖关系。

## 特性

- 简单易用。
- 高效的数据依赖处理。
- 支持任务之间的数据依赖关系。
- 支持任务之间的数据传递。
- 支持并行和串行模式的快速切换。
- 支持多进程模式中的异常统一处理。
- 支持自定义任务执行器。

## 待办事项

- [ ] 添加更好的异常抛出逻辑。
- [x] 更新Task支持直接传入execute_requires并能够解析args/kwargs。
- [x] 扩展Data定义，支持从一个对象中获取多个数据（Unpack）。
- [ ] 添加更多的测试用例。
- [ ] 添加更多的文档。
- [x] 添加更多的示例。

## 快速上手

安装TaskBox：

```bash
    pip install taskbox
```

使用TaskBox：

```python
# exeamples/quickstart.py

from taskbox import Task, ParallelTaskBox


class Task1(Task):
    def execute(self, data1: int):
        result = data1 + 1
        # 将结果保存到共享数据中
        self.shared.set("data1", result)
        return result


class Task2(Task):
    def execute(self, data2: int):
        # 等待Task1完成并获取其结果
        data1 = self.shared.get("data1")
        return data2 * data1


if __name__ == "__main__":
    # 创建TaskBox
    taskbox = ParallelTaskBox()

    # 提交任务: 1. 逐个提交
    taskbox.add_task(Task1(execute_requires=(1,)))
    taskbox.add_task(Task2(execute_requires=(2,)))

    # 提交任务：2. 定义任务参数
    taskbox.reset()
    task_dict = {Task1: (1,), Task2: (2,)}
    taskbox.add_tasks(task_dict)

    # 开始运行、设置单个任务的超时时间、设置回调函数打印结果、堵塞等待完成
    taskbox.start(timeout=8, callback_func=lambda x: print(x)).wait()

```

> 更多示例请参考[examples](./examples/README.md)目录。

## 许可证

本项目基于 LGPL 许可证进行分发。有关详细信息，请参阅 [LICENSE](./LICENSE) 文件。