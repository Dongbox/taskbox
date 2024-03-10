import time
from taskbox import Task, Data


class Test1(Task):
    def run(self, source_data: str):
        # self.set_data("test1", self.source_data)
        print("start")
        # raise ValueError("test2 error")

        time.sleep(10)
        return {"test1": "test1"}


class Test2(Task):
    def run(self, source_data: str):
        # raise SystemExit("test2 error")
        print(self.get_data("test1"))
        # print(self.get_data('test2'))
        return {"test2": "test2"}


if __name__ == "__main__":
    # 测试
    test = Test1()
    test.set_func_args(Data("source"))
    test.set_timeout(3)
    test.start()
