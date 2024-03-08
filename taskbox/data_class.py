# -*- coding: utf-8 -*-
"""
File: data_class.py
Author: Dongbox
Date: 2024-03-08
Description:
    Data class to fetch value from data
    
"""
from typing import Any


class Data:
    """
    Data class to fetch value from data
    E.g
        1. Fetch value from dictionary
            data = {'name': 'Dongbox'}
            name = Data(data, 'name')
            print(name.value) # Dongbox

            df_dict = {"i_source": DataFrame(data={"a": [1, 2, 3], "b": [4, 5, 6]})}
            i_source = Data(df_dict, 'i_source')
            print(i_source.value) # DataFrame(data={"a": [1, 2, 3], "b": [4, 5, 6]})

        2. Fetch value from object
            class Person:
                def __init__(self, name, age):
                    self.name = name
                    self.age = age

            person = Person('Dongbox', 30)
            name = Data(person, 'name')
            print(name.value) # Dongbox

        3. Fetch value from python basic type(int, float, str.)
            data = 10
            value = Data(data)
            print(value.value) # 10

    """

    def __init__(self, data: Any, name: str = None) -> None:
        self.__data = data
        self.__name = name

    @property
    def value(self) -> Any:
        """
        Property method to fetch value from data
        """
        if self.__name is not None:
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
        else:
            return self.__data
