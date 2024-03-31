import taskbox as tb
import pandas as pd


# This task is a pre-task will provide shared data for the last task
class PreTask(tb.Task):
    def execute(self, job_data: pd.DataFrame, user_data: pd.DataFrame):
        # Merge the dataframes
        merged_df = pd.merge(job_data, user_data, left_on="job_id", right_on="user_id")

        # Set the shared data for the last task
        self.shared.set("merged_df", merged_df)

        # Return its result and save
        return {"merged_df": merged_df}


# The last task has dependencies on the shared data from the previous task.
class LastTask(tb.Task):
    def execute(self, mock_data1: pd.DataFrame, mock_data2: pd.DataFrame):
        # Do its own calculation at first
        result = pd.concat([mock_data1, mock_data2], axis=0)

        # Wait for the shared data when it has finished all isolaterd tasks below.
        merged_df = self.shared.get("merged_df")

        # Merge the two dataframes
        result = pd.merge(merged_df, result, left_on="job_id", right_on="mock_id")

        # Retuen
        return {"final_df": result}


if __name__ == "__main__":
    # Define the mock data dictionary
    data_dict = {
        "job": pd.DataFrame(
            {"job_id": [1, 2, 3], "job_name": ["job1", "job2", "job3"]}
        ),
        "user": pd.DataFrame(
            {"user_id": [1, 2, 3], "user_name": ["user1", "user2", "user3"]}
        ),
        "mock_data1": pd.DataFrame(
            {"mock_id": [1, 2, 3], "mock_name": ["mock1", "mock2", "mock3"]}
        ),
        "mock_data2": pd.DataFrame(
            {"mock_id": [1, 2, 3], "mock_name": ["mock1", "mock2", "mock3"]}
        ),
    }

    # Use Collection to dynamically pass the data to the task(It will fetch the data when the task acess it.)
    task_dict = {
        PreTask: [tb.Unpack(data_dict, ["job", "user"])],
        LastTask: [tb.Unpack(data_dict, ["mock_data1", "mock_data2"])],
    }

    # Define the task graph
    task_box = tb.ParallelTaskBox()
    task_box.add_tasks(task_dict)

    # Initialize the result dictionary
    result = {}

    # Run the task graph, and define the callback function to update the result dictionary
    task_box.start(10, callback_func=lambda x: result.update(x)).wait()

    # Print the result
    print(result.keys())
    print(result.values())
