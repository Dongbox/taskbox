from taskbox import Data, SeriesTaskBox, Task
from task_definitions import PrintTask, PrintInteractiveTask


if __name__ == "__main__":
    # Example for Task Dict
    tasks = {
        PrintTask: [Data("Print str in series task")],
        PrintInteractiveTask: [Data("Interactive task in series task")],
    }
    # Define a SeriesTaskBox
    task_box = SeriesTaskBox()

    # Submit tasks to the SeriesTaskBox
    task_box.add_tasks(tasks)

    # Start the SeriesTaskBox with a timeout of 8 seconds
    task_box.start(timeout=8, callback_func=lambda x: print(x))

    print("Waiting for all tasks to finish")
