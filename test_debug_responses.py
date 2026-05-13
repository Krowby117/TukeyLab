import sys
sys.path.insert(0, '/Users/gavindominique/Documents/TukeyLab')
import json
from pathlib import Path
import pandas as pd
from components.project_ai import DatasetCatalogController

project = Path('/Users/gavindominique/Documents/TukeyLab/projects/test_95917c527/data')
dfs = {}
for p in project.iterdir():
    if p.suffix.lower()=='.csv':
        dfs[p.name]=pd.read_csv(p)

print("Loaded datasets:", list(dfs.keys()))
controller = DatasetCatalogController(lambda: dfs)

# Test 4: non-existent dataset
print("\n[Test 4]")
resp = controller.process_message('Create a graph from dataset_that_does_not_exist.csv')
print(f"Response type: {type(resp)}")
print(f"Response (first 200 chars): {resp[:200]}")
try:
    obj = json.loads(resp)
    print(f"JSON parsed: action={obj.get('action')}")
except:
    print("Not valid JSON")

# Test 5: missing column
print("\n[Test 5]")
resp = controller.process_message('Create scatter of missing_col vs tempo from spotify_analysis_dataset.csv')
print(f"Response type: {type(resp)}")
try:
    obj = json.loads(resp)
    print(f"JSON parsed: action={obj.get('action')}")
    if obj.get('action') == 'error':
        print(f"  Error code: {obj['error']['code']}")
except:
    print("Not valid JSON")

