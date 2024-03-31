import taskbox as tb

# From Dict
collection = tb.Unpack(
    data={"name": "John", "age": 25},
    names=["name"],
)

print("Dict Type: ", *collection)  # ['John']

try:
    collection["age"]
except KeyError as e:
    print("Dict Error: ", e)

# From Data
collection = tb.Unpack(
    data=tb.Data({"name": "John", "age": 25}),
    names=["name", "age"],
)

print("Data Type: ", *collection)  # ['John', 25]
