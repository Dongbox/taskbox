import unittest
from taskbox.task import Task


class TaskTests(unittest.TestCase):
    def test_run_method_not_implemented(self):
        task = Task()
        with self.assertRaises(NotImplementedError):
            task.execute()

    def test_task_not_started(self):
        task = Task()
        with self.assertRaises(ValueError):
            task.wait()

    def test_task_timeout(self):
        def long_running_task():
            import time

            time.sleep(5)

        task = Task(timeout=3)
        task.execute = long_running_task

        with self.assertRaises(TimeoutError):
            task.start(wait=True)

    def test_task_completed_successfully(self):
        def successful_task():
            return "Task completed successfully"

        task = Task()
        task.execute = successful_task

        result = task.start(wait=True)
        self.assertEqual(result, "Task completed successfully")

    def test_task_callback_function(self):
        def callback(result):
            self.assertEqual(result, "Task completed successfully")

        def successful_task():
            return "Task completed successfully"

        task = Task()
        task.execute = successful_task

        task.start(wait=False, callback_func=callback)

    def test_task_with_arguments(self):
        def task_with_arguments(arg1, arg2):
            return arg1 + arg2

        task = Task()
        task.set_execute_required((2, 3))
        task.execute = task_with_arguments

        result = task.start(wait=True)
        self.assertEqual(result, 5)

    def test_task_join_with_timeout(self):
        def long_running_task():
            import time

            time.sleep(5)

        task = Task(timeout=3)
        task.execute = long_running_task

        with self.assertRaises(TimeoutError):
            task.start(wait=False)
            task.wait()

    def test_task_join_without_timeout(self):
        def successful_task():
            return "Task completed successfully"

        task = Task()
        task.execute = successful_task

        task.start(wait=False)
        task.wait()

        self.assertEqual(task.result, "Task completed successfully")


if __name__ == "__main__":
    unittest.main()
