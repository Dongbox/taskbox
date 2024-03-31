# Copyright (c) 2023, 2024 Dongbo Xie All Rights Reserved.
#
# Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
# LICENSE, otherwise it is available at <https://github.com/Dongbox/taskbox/LICENSE>.

from typing import Any, Optional, Sequence


# Fetch value from a data
class Data:
    """
    Data class to fetch value from data.

    Args:
        data (Any): The data from which to fetch the value.
        name (Optional[str]): The name or key to fetch the value from the data. Defaults to None.

    Raises:
        TypeError: If the name is not a string.
        KeyError: If the name is not found in the dictionary data.
        AttributeError: If the name is not found as an attribute in the data object.

    Examples:
        1. Fetch value from dictionary:
            data = {'name': 'Dongbox'}
            name = Data(data, 'name')
            print(name.value)  # Dongbox

            df_dict = {"i_source": DataFrame(data={"a": [1, 2, 3], "b": [4, 5, 6]})}
            i_source = Data(df_dict, 'i_source')
            print(i_source.value)  # DataFrame(data={"a": [1, 2, 3], "b": [4, 5, 6]})

        2. Fetch value from object:
            class Person:
                def __init__(self, name, age):
                    self.name = name
                    self.age = age

            person = Person('Dongbox', 30)
            name = Data(person, 'name')
            print(name.value)  # Dongbox

        3. Fetch value from python basic type (int, float, str):
            data = 10
            value = Data(data)
            print(value.value)  # 10
    """

    def __init__(self, data: Any, name: Optional[str] = None) -> None:
        self.__data = data
        self.__name = name

        # Check if name is not None
        if self.__name is not None:
            if not isinstance(self.__name, str):
                raise TypeError("Index must be a string")

            # Check if data is a dictionary
            if isinstance(self.__data, dict):
                # Check if name is not in dictionary keys
                if self.__name not in self.__data.keys():
                    raise KeyError(
                        f"'{self.__name}' not found in '{self.__data.keys()}'"
                    )
            else:
                # Check if name is not in data attributes
                if not hasattr(self.__data, self.__name):
                    raise AttributeError(
                        f"'{self.__data}' object has no attribute '{self.__name}'"
                    )

    @property
    def value(self) -> Any:
        """
        Property method to fetch value from data.

        Returns:
            The value fetched from the data.

        Raises:
            KeyError: If the key is not found in the data.
            AttributeError: If the attribute is not found in the data.
        """
        if self.__name is None:
            return self.__data

        try:
            # If data is a dictionary, fetch value by key
            if isinstance(self.__data, dict):
                return self.__data[self.__name]
            else:
                # Fetch attribute value from data
                return getattr(self.__data, self.__name)
        except KeyError:
            # If key not found, raise KeyError
            raise KeyError(f"'{self.__name}' not found in '{self.__data.keys()}'")
        except AttributeError:
            # If attribute not found, raise AttributeError
            raise AttributeError(
                f"'{self.__data}' object has no attribute '{self.__name}'"
            )


# Fetch multi value from a data
class Unpack:
    """
    A class that provides a convenient way to access attributes or items from a data object.

    Args:
        data (Any): The data object from which to extract attributes or items.
        names (Sequence): A sequence of attribute or item names to extract from the data object.

    Raises:
        TypeError: If the key provided is not a string.
        KeyError: If the key provided is not found in the names sequence.

    Returns:
        Any: The value of the attribute or item corresponding to the provided key.

    """

    def __init__(self, data: Any, names: Sequence) -> None:
        self.__data = data
        self.__names = names

    def __getitem__(self, key: str) -> Any:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        if key not in self.__names:
            raise KeyError(f"'{key}' not found in names: {self.__names}")

        if isinstance(self.__data, dict):
            return self.__data[key]
        elif isinstance(self.__data, Data):
            return self.__data.value[key]
        else:
            return getattr(self.__data, key)

    def __iter__(self):
        # Return an iterator over the attribute names with their values
        for name in self.__names:
            yield self[name]
