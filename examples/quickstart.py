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
