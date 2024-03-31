# Copyright (c) 2023, 2024 Dongbo Xie All Rights Reserved.
#
# Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
# LICENSE, otherwise it is available at <https://github.com/Dongbox/taskbox/LICENSE>.

from abc import abstractmethod
from typing import Any, Dict
import time

from multiprocessing.managers import SyncManager


class SharedData:
    @abstractmethod
    def get(self, name: str):
        """
        Abstract method to get the value of the shared data with the specified name.

        Args:
            name (str): The name of the shared data.

        Returns:
            Any: The value of the shared data.

        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, name: str, value: Any):
        """
        Abstract method to set the value of the shared data with the specified name.

        Args:
            name (str): The name of the shared data.
            value (Any): The value to be set.

        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        """
        raise NotImplementedError


class ParallelSharedDict(SharedData):
    def __init__(self, manager: SyncManager):
        """
        Initializes a SharedDict object.

        Args:
            manager (SyncManager): The SyncManager object used for synchronization.
        """
        self._shared_data = manager.dict()

    def _get_shared_data(self) -> Dict:
        """
        Gets the shared data dictionary.

        Returns:
            Dict: The shared data dictionary.

        Raises:
            ValueError: If the shared data is not set.
        """
        if self._shared_data is None:
            raise ValueError("Shared data not set")
        return self._shared_data

    def get(self, name: str) -> Any:
        """
        Gets the value of the shared data with the specified name.

        Args:
            name (str): The name of the shared data.

        Returns:
            Any: The value of the shared data.

        Raises:
            ValueError: If the shared data is not set.
        """
        shared_data = self._get_shared_data()
        while True:
            result = shared_data.get(name)
            if result is not None:
                return result
            time.sleep(0.1)

    def set(self, name: str, value: Any):
        """
        Sets the value of the shared data with the specified name.

        Args:
            name (str): The name of the shared data.
            value (Any): The value to be set.

        Raises:
            ValueError: If the shared data is not set.
        """
        shared_data = self._get_shared_data()
        shared_data[name] = value
        self._shared_data = shared_data


class SerialSharedDict(SharedData):
    def __init__(self):
        """
        Initializes a SeriesSharedDict object.
        """
        self._shared_data = {}

    def get(self, name: str) -> Any:
        """
        Gets the value of the shared data with the specified name.

        Args:
            name (str): The name of the shared data.

        Returns:
            Any: The value of the shared data.

        Raises:
            ValueError: If the shared data is not set.
        """
        if self._shared_data is None:
            raise ValueError("Shared data not set")
        return self._shared_data.get(name)

    def set(self, name: str, value: Any):
        """
        Sets the value of the shared data with the specified name.

        Args:
            name (str): The name of the shared data.
            value (Any): The value to be set.

        Raises:
            ValueError: If the shared data is not set.
        """
        if self._shared_data is None:
            raise ValueError("Shared data not set")
        self._shared_data[name] = value
