from taskbox import Data, ParallelTaskBox
from task_definitions import PrintTask, PrintInteractiveTask


if __name__ == "__main__":
    # Example for Task Dict
    tasks = {
        PrintTask: [Data("Print str in parallel task")],
        PrintInteractiveTask: [Data("Interactive task in parallel task")],
    }

    # Define a ParallelTaskBox
    task_box = ParallelTaskBox()

    # Submit tasks to the ParallelTaskBox
    for task, data_list in tasks.items():
        task_box.submit_task(task(execute_required=data_list))

    # Start the ParallelTaskBox with a timeout of 8 seconds
    task_box.start(timeout=8, callback_func=lambda x: print(x))

    # Wait for all tasks to finish
    task_box.wait()
