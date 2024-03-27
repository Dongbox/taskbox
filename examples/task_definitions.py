import time
from taskbox import Task, Data


class PrintTask(Task):
    def execute(self, mock_data: Data):

        self.shared_data.set("sha", mock_data)
        print(mock_data.value)

        # Mock a long running task
        time.sleep(5)

        return "Return String from PrintTask"


class PrintInteractiveTask(Task):
    def execute(self, mock_data: Data):
        print(mock_data.value)

        sha_from_print_task: Data = self.shared_data.get("sha")
        print("Data from other task: ", sha_from_print_task.value)

        # Mock dict type
        return {"key": "value"}
