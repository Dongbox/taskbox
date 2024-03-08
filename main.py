import time
from taskbox import Task


class Test1(Task):
    def __init__(self, source_data: str) -> None:
        super().__init__()
        self.source_data = source_data

    def run(self):
        # self.set_data("test1", self.source_data)
        print("start")
        time.sleep(10)
        return {"test1": "test1"}


class Test2(Task):
    def run(self):
        raise ValueError("test2 error")
        print(self.get_data("test1"))
        # print(self.get_data('test2'))
        return {"test2": "test2"}


if __name__ == "__main__":
    # 测试
    test = Test1("source")
    test.start()
    test.terminate()