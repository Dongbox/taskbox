import time
from taskbox import Task, Data, TaskBox, ParallelTaskBox, SeriesTaskBox


class Test1(Task):
    def execute(self, source_data: Data):
        # raise ValueError("test1 error")

        self._shared_data.set("sha", source_data)
        print(source_data.value)
        time.sleep(5)
        print("Finished")
        # time.sleep(10)
        return {"test1": "test1"}


class Test2(Task):
    def execute(self, source_data: Data):
        # raise SystemExit("test2 error")
        print(source_data.value)
        sha_from_test1: Data = self._shared_data.get("sha")
        print("From Test1: ", sha_from_test1.value)
        # time.sleep(10)
        # print(self.get_data('test2'))
        return {"test2": "test2"}


if __name__ == "__main__":
    # 测试
    test1 = Test1()
    test1.set_func_args(Data("test1->str"))
    # test1.set_callback(lambda x: print(type(x)))

    test2 = Test2()
    test2.set_func_args(Data("test2->str"))
    # Example for TaskBox
    task_box = ParallelTaskBox()
    # task_box.add_callback_func(lambda x: print(x))
    task_box.submit_task(test1)
    task_box.submit_task(test2)
    task_box.start(timeout=8)
    task_box.wait()

    # Example for Task
    # test1.set_func_args((Data("test1->str"), ))
    # test1.start()
