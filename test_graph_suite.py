import sys, json
sys.path.insert(0, '/Users/gavindominique/Documents/TukeyLab')
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from components.project_ai import DatasetCatalogController

project = Path('/Users/gavindominique/Documents/TukeyLab/projects/test_95917c527/data')
dfs = {p.name: pd.read_csv(p) for p in project.iterdir() if p.suffix.lower() == '.csv'}
ctrl = DatasetCatalogController(lambda: dfs)

tests = [
    # (prompt, expected_action, expected_chart_type)
    ("Create a scatter plot of tempo vs valence from spotify_analysis_dataset.csv", "create_graph", "scatter"),
    ("Create a histogram of loudness from spotify_analysis_dataset.csv",            "create_graph", "histogram"),
    ("Create a violin plot of energy from spotify_analysis_dataset.csv",            "create_graph", "violin"),
    ("Create a line chart of tempo vs valence from spotify_analysis_dataset.csv",   "create_graph", "line"),
    ("Create a bar chart of Item vs Quantity Sold from dirty_cafe_sales.csv",       "create_graph", "bar"),
    ("Create a box plot of tempo from spotify_analysis_dataset.csv",                "create_graph", "box"),
    ("Create a pie chart of Item from dirty_cafe_sales.csv",                        "create_graph", "pie"),
    ("Create a heatmap of tempo vs energy from spotify_analysis_dataset.csv",       "create_graph", "heatmap"),
    ("Create a graph from dataset_that_does_not_exist.csv",                         "error",        None),
    ("Create scatter of missing_col vs tempo from spotify_analysis_dataset.csv",    "error",        None),
    ("What datasets are available?",                                                "text",         None),
]

print("=" * 70)
all_pass = True
for i, (prompt, exp_action, exp_chart) in enumerate(tests, 1):
    resp = ctrl.process_message(prompt)
    try:
        obj = json.loads(resp)
        action = obj.get("action", "unknown")
        chart = obj.get("graph_request", {}).get("intent", {}).get("chart_type")

        # Also verify figure_json is Plotly-compatible for create_graph
        plotly_ok = ""
        if action == "create_graph":
            try:
                go.Figure(obj["graph_request"]["figure_json"])
                plotly_ok = " [go.Figure ✓]"
                # Verify correct columns used
                x_assigned = obj["graph_request"]["intent"]["columns"].get("x")
                y_assigned = obj["graph_request"]["intent"]["columns"].get("y")
                plotly_ok += f" x={x_assigned} y={y_assigned}"
            except Exception as e:
                plotly_ok = f" [go.Figure FAIL: {e}]"

        passed = (
            (exp_action == "text" and action not in ["create_graph", "error"]) or
            (exp_action == "error" and action == "error") or
            (exp_action == "create_graph" and action == "create_graph" and (exp_chart is None or chart == exp_chart))
        )
    except json.JSONDecodeError:
        action, chart, plotly_ok = "text", None, ""
        passed = exp_action == "text"

    status = "✅" if passed else "❌"
    if not passed:
        all_pass = False
    print(f"{status} [{i:02}] {action}/{chart}{plotly_ok}")
    if not passed:
        print(f"      expected {exp_action}/{exp_chart}")
        print(f"      prompt: {prompt}")

print("=" * 70)
print("ALL PASS" if all_pass else "SOME FAILED")

