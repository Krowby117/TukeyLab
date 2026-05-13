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

test_cases = [
    ("Create a scatter plot of tempo vs valence from spotify_analysis_dataset.csv", "scatter"),
    ("Create a histogram of loudness from spotify_analysis_dataset.csv", "histogram"),
    ("Create a violin plot of energy by mode from spotify_analysis_dataset.csv", "error"),
    ("Create a graph from dataset_that_does_not_exist.csv", "error"),
    ("Create scatter of missing_col vs tempo from spotify_analysis_dataset.csv", "error"),
    ("What datasets are available?", "text"),
]

print("=" * 70)
print("VALIDATION TESTS")
print("=" * 70)

for idx, (prompt, expected) in enumerate(test_cases, 1):
    print(f"\n[Test {idx}] Prompt: {prompt}")
    print(f"Expected: {expected}")

    resp = controller.process_message(prompt)

    try:
        obj = json.loads(resp)
        action = obj.get('action', 'unknown')
        print(f"Result: action={action}")

        if action == 'create_graph':
            chart_type = obj['graph_request']['intent']['chart_type']
            print(f"        chart_type={chart_type}")
        elif action == 'error':
            print(f"        error_code={obj['error']['code']}")

        # Check expectation
        if expected == "text" and action not in ["create_graph", "error"]:
            print("✅ PASS (text response)")
        elif expected == "error" and action == "error":
            print("✅ PASS (error as expected)")
        elif expected == action:
            print("✅ PASS")
        else:
            print(f"❌ FAIL (expected {expected}, got {action})")
    except json.JSONDecodeError:
        print(f"Result: raw text (not JSON)")
        if expected == "text":
            print("✅ PASS (text response)")
        else:
            print(f"❌ FAIL (expected {expected}, got raw text)")

print("\n" + "=" * 70)

