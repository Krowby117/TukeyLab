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

controller = DatasetCatalogController(lambda: dfs)
resp = controller.process_message('create graph showing total quantity of each item purchased in dirty_cafe_sales')
obj = json.loads(resp)
print("Action:", obj['action'])
if obj['action'] == 'create_graph':
    print("Chart type:", obj['graph_request']['intent']['chart_type'])
    print("Success! Bar chart request created.")
else:
    print("Error detail:", obj['error']['detail'])

