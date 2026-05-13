from __future__ import annotations

import json

import pandas as pd

from components.project_ai import DatasetCatalogController


def _controller() -> DatasetCatalogController:
    df = pd.DataFrame(
        {
            "tempo": [120, 130, 140],
            "valence": [0.4, 0.7, 0.5],
            "energy": [0.8, 0.6, 0.9],
        }
    )
    return DatasetCatalogController(lambda: {"spotify_analysis_dataset.csv": df})


def run_smoke_tests() -> None:
    controller = _controller()

    list_resp = controller.process_message("What datasets are available?")
    assert "spotify_analysis_dataset.csv" in list_resp

    graph_resp = controller.process_message(
        "Create a scatter plot of tempo vs valence from spotify_analysis_dataset.csv"
    )
    payload = json.loads(graph_resp)

    assert payload["schema_version"] == "1.0"
    assert payload["action"] == "create_graph"
    assert payload["graph_request"]["sources"] == ["spotify_analysis_dataset.csv"]

    figure_json = payload["graph_request"]["figure_json"]
    assert isinstance(figure_json.get("data"), list)
    assert figure_json["data"][0]["type"] == "scatter"

    print("project_ai graph JSON smoke tests passed")


if __name__ == "__main__":
    run_smoke_tests()

