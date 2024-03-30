import taskbox as tb

# From Dict
collection = tb.Collection(
    data={"name": "John", "age": 25},
    names=["name"],
)

print("Dict: ", collection["name"])  # ['John', 25]
try:
    collection["age"]
except KeyError as e:
    print("Dict Error: ", e)

# From Data
collection = tb.Collection(
    data=tb.Data({"name": "John", "age": 25}),
    names=["name", "age"],
)

print("Data: ", collection["name"])  # ['John', 25]
