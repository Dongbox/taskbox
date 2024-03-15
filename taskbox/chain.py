
from typing import Generator, List, Dict
from task import Task

class TaskChain:
    def __init__(self, task_dependencies: Dict[Task, List[Task]]):
        # 遍历更新任务依赖为task.ident
        self.tasks = task_dependencies

    def get_execution_order(self) -> Generator[List[Task], None, None]:
        # List of tasks with no dependencies
        queue = [task for task, deps in self.tasks.items() if not deps]
        result = []

        while queue:
            parallel_tasks = []
            for _ in range(len(queue)):
                task = queue.pop(0)
                parallel_tasks.append(task)
                result.append(task)

                successors = [successor for successor, dependencies in self.tasks.items() if task in dependencies]
                for successor in successors:
                    self.tasks[successor].remove(task)
                    # If successor has no more dependencies, add it to the queue
                    if not self.tasks[successor]:
                        queue.append(successor)
            yield parallel_tasks

        # Check for cycle
        if len(result) != len(self.tasks):
            raise Exception("Tasks have a cycle")



if __name__ == "__main__":
    # Example
    class MyTask(Task):
        def run(self, *args, **kwargs):
            print("Running task")
            return "Task finished"
        
    class MyTask1(Task):
        def run(self, *args, **kwargs):
            print("Running task")
            return "Task finished"
        
    class MyTask2(Task):
        def run(self, *args, **kwargs):
            print("Running task")
            return "Task finished"
        
    task = MyTask()
    task1 = MyTask1()
    task2 = MyTask2()

    # more complecity
    chain = TaskChain({
        task: [task2],
        task1: [],
        task2: [task, task1]
    })

    for tasks in chain.get_execution_order():
        print(tasks)  # Prints a list of tasks that can be executed in parallel
