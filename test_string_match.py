import sys
sys.path.insert(0, '/Users/gavindominique/Documents/TukeyLab')

# Check the string matching
msg = "Create a graph from dataset_that_does_not_exist.csv"
lower = msg.lower()
print(f"Message: {msg}")
print(f"Lower: {lower}")
print(f"'create graph' in lower: {'create graph' in lower}")

# Check if it's detected as a graph request
checks = (
    "create graph",
    "make graph",
    "create chart",
    "make chart",
    "plot",
    "scatter",
    "histogram",
    "line chart",
    "bar chart",
    "box plot",
    "heatmap",
    "violin",
)
result = any(text in lower for text in checks)
print(f"Graph request detected: {result}")

