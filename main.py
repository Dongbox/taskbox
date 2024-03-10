import time
from taskbox import Task, Data, TaskBox


class Test1(Task):
    def run(self, source_data: Data):
        self.set_data("sha", source_data)
        # print(source_data.value)
        time.sleep(3)

        # raise ValueError("test1 error")
        # time.sleep(10)
        return {"test1": "test1"}


class Test2(Task):
    def run(self, source_data: Data):
        # raise SystemExit("test2 error")
        print(source_data.value)
        print("From Test1: ", self.get_data("sha").value)
        time.sleep(10)
        # print(self.get_data('test2'))
        return {"test2": "test2"}


if __name__ == "__main__":
    # 测试
    test1 = Test1()
    test2 = Test2()

    task_box = TaskBox()
    task_box.submit_task(test1, lambda x: print(x), Data("test1->str"))
    task_box.submit_task(test2, lambda x: print(x), Data({"test2": "dict"}))
    task_box.start()
    task_box.wait()
