from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

import pandas as pd


class DatasetCatalogController:
    REFUSAL_MESSAGE = (
        "Phase 1 assistant scope supports dataset catalog requests and graph JSON requests. "
        "Try: 'What datasets are available?', 'Describe <dataset>', or "
        "'Create a scatter plot for <dataset>'."
    )

    def __init__(self, get_dataframes: Callable[[], dict[str, pd.DataFrame]]):
        self._get_dataframes = get_dataframes

    def process_message(self, prompt: str) -> str:
        message = (prompt or "").strip()
        if not message:
            return "Please enter a question."

        dataframes = self._get_dataframes()
        if not dataframes:
            return "No datasets are loaded in this project yet."

        if self._is_list_request(message):
            return self._build_dataset_catalog(dataframes)

        if self._is_graph_request(message):
            return self._build_graph_request_payload(message, dataframes)

        matched = self._match_dataset_name(message, dataframes)
        if matched:
            return self._describe_dataset(matched, dataframes[matched])

        return self.REFUSAL_MESSAGE

    def _is_list_request(self, message: str) -> bool:
        lower = message.lower()
        checks = (
            "what datasets",
            "which datasets",
            "list datasets",
            "available datasets",
            "data sources",
            "what files",
        )
        return any(text in lower for text in checks)

    def _is_graph_request(self, message: str) -> bool:
        lower = message.lower()
        checks = (
            "create graph",
            "create a graph",
            "make graph",
            "make a graph",
            "create chart",
            "create a chart",
            "make chart",
            "make a chart",
            "plot",
            "scatter",
            "histogram",
            "line chart",
            "bar chart",
            "box plot",
            "heatmap",
            "violin",
            "pie chart",
            "pie graph",
            "pie",
            "funnel",
            "sunburst",
            "treemap",
            "bubble chart",
            "area chart",
        )
        return any(text in lower for text in checks)

    def _detect_chart_type(self, lower: str) -> str:
        if "hist" in lower:
            return "histogram"
        elif "violin" in lower:
            return "violin"
        elif "box" in lower:
            return "box"
        elif "heat" in lower or "density" in lower:
            return "heatmap"
        elif "funnel" in lower:
            return "funnel"
        elif "sunburst" in lower:
            return "sunburst"
        elif "treemap" in lower:
            return "treemap"
        elif "bubble" in lower:
            return "bubble"
        elif "area" in lower:
            return "area"
        elif "pie" in lower or "donut" in lower or "doughnut" in lower:
            return "pie"
        elif "line" in lower:
            return "line"
        elif any(w in lower for w in ("bar", "count", "total", "sum", "each", "per", "breakdown")):
            return "bar"
        else:
            return "scatter"

    def _extract_columns_from_prompt(
        self, message: str, all_cols: list[str], numeric_cols: list[str]
    ) -> dict[str, str | list[str] | None]:
        """Extract specific column assignments from a user prompt.

        Returns: {"x": col_name, "y": col_name, "color": col_name}
        Falls back to first available columns when not specified.
        """
        import re

        lower_msg = message.lower()
        lower_col_map = {col.lower(): col for col in all_cols}

        # Strip "from <dataset>" fragments so filenames don't interfere
        clean_msg = re.sub(r'\bfrom\s+\S+', '', lower_msg).strip()

        # --- Full-text scan: find all column names present in the prompt in order ---
        # Sort by length descending so longest (most specific) columns match first
        found_in_order: list[str] = []
        remaining = clean_msg
        for col_lower in sorted(lower_col_map.keys(), key=len, reverse=True):
            if col_lower in remaining:
                found_in_order.append(lower_col_map[col_lower])
                remaining = remaining.replace(col_lower, " " * len(col_lower))

        x_col: str | None = None
        y_col: str | None = None
        color_col: str | None = None

        # --- "X vs Y" ordering: left side = x, right side = y ---
        for sep in [" vs ", " v ", " against ", " versus "]:
            if sep in clean_msg:
                left_frag, right_frag = clean_msg.split(sep, 1)
                # Walk found_in_order in document order and use positional split
                left_set = {lower_col_map[lc] for lc in lower_col_map if lc in left_frag}
                right_set = {lower_col_map[lc] for lc in lower_col_map if lc in right_frag}
                # Assign first discovered in each side
                for col in found_in_order:
                    if col in left_set and x_col is None:
                        x_col = col
                    elif col in right_set and y_col is None:
                        y_col = col
                break

        # --- "of X" for single-column charts (histogram of tempo) ---
        if x_col is None and " of " in clean_msg:
            for part in clean_msg.split(" of ")[1:]:
                part_clean = part.split("from")[0].strip()
                for col_lower in sorted(lower_col_map.keys(), key=len, reverse=True):
                    if col_lower in part_clean:
                        x_col = lower_col_map[col_lower]
                        break
                if x_col:
                    break

        # --- Fall back to document order if vs-pattern not found ---
        if x_col is None and len(found_in_order) >= 1:
            x_col = found_in_order[0]
        if y_col is None and len(found_in_order) >= 2:
            y_col = found_in_order[1]

        # --- "color by Z" ---
        for phrase in [" color by ", " colour by ", " colored by ", " coloured by "]:
            if phrase in lower_msg:
                after = lower_msg.split(phrase)[-1].split()[0]
                for lc, orig in lower_col_map.items():
                    if after in lc or lc in after:
                        color_col = orig
                        break

        # --- Fallback to first numeric/available columns ---
        if x_col is None and numeric_cols:
            x_col = numeric_cols[0]
        if y_col is None and len(numeric_cols) > 1:
            y_col = numeric_cols[1]
        elif y_col is None and len(all_cols) > 1:
            y_col = all_cols[1]

        return {"x": x_col, "y": y_col, "color": color_col}

    def _check_for_invalid_columns(self, message: str, available_cols: list[str]) -> str | None:
        lower_msg = message.lower()
        lower_cols = [col.lower() for col in available_cols]

        # Look for patterns like "column_name" that aren't in the dataset
        words = lower_msg.split()
        for word in words:
            if word not in ["a", "the", "of", "in", "from", "to", "vs", "and", "or", "by", "with"]:
                if word not in lower_cols and any(c.isalpha() for c in word):
                    # Might be a column name the user mentioned
                    # Check if it's close to any available column
                    if not any(word in col or col in word for col in lower_cols):
                        # Check if the user explicitly said a column name
                        if any(phrase in lower_msg for phrase in [f"column {word}", f"{word} column", f"{word} from", f"{word} vs"]):
                            return f"Column '{word}' not found. Available columns: {', '.join(sorted(available_cols))}"

        return None

    def _validate_mentioned_columns(self, message: str, available_cols: list[str]) -> str | None:
        lower_msg = message.lower()
        lower_cols = [col.lower() for col in available_cols]

        # Words that are never column names — chart keywords, prepositions, common words
        skip_words = {
            "a", "the", "from", "in", "on", "of", "to", "for", "and", "or", "by", "with",
            "plot", "scatter", "histogram", "chart", "graph", "create", "make", "show",
            "vs", "v", "between", "comparing", "showing", "using", "dataset", "file",
            "csv", "json", "xlsx", "line", "bar", "box", "pie", "area", "violin",
            "heatmap", "bubble", "funnel", "sunburst", "treemap", "density",
            "each", "total", "sum", "count", "per", "breakdown", "distribution",
        }

        potential_cols: set[str] = set()

        # "X vs Y" or "X v Y" — both X and Y are potential column names
        for sep in [" vs ", " v ", " against ", " versus "]:
            if sep in lower_msg:
                parts = lower_msg.split(sep)
                for part in parts:
                    words = part.strip().split()
                    for w in reversed(words):
                        cleaned = w.rstrip(".,;:()[]").split("/")[-1]
                        if (cleaned and cleaned not in skip_words and len(cleaned) > 1
                                and not any(cleaned.endswith(ext) for ext in [".csv", ".json", ".xlsx"])):
                            potential_cols.add(cleaned)
                            break

        # "of X" — only the part AFTER "of" is a column name (e.g. "histogram of tempo")
        if " of " in lower_msg:
            for part in lower_msg.split(" of ")[1:]:  # skip left side — it's chart type or preposition
                for w in part.strip().split():
                    cleaned = w.rstrip(".,;:()[]").split("/")[-1]
                    if (cleaned and cleaned not in skip_words and len(cleaned) > 1
                            and not any(cleaned.endswith(ext) for ext in [".csv", ".json", ".xlsx"])):
                        potential_cols.add(cleaned)
                        break

        # Validate each potential column against available columns
        for potential_col in potential_cols:
            if potential_col not in lower_cols:
                close = [col for col in available_cols
                         if potential_col in col.lower() or col.lower() in potential_col]
                if not close:
                    return (
                        f"Column '{potential_col}' not found in dataset. "
                        f"Available columns: {', '.join(sorted(available_cols[:10]))}..."
                    )

        return None

    def _match_dataset_name(self, message: str, dataframes: dict[str, pd.DataFrame]) -> str | None:
        lower = message.lower()

        # Exact filename match first.
        for filename in dataframes:
            if filename.lower() in lower:
                return filename

        stem_matches = []
        for filename in dataframes:
            stem = Path(filename).stem.lower()
            if stem and stem in lower:
                stem_matches.append(filename)

        if len(stem_matches) == 1:
            return stem_matches[0]

        return None

    def _build_dataset_catalog(self, dataframes: dict[str, pd.DataFrame]) -> str:
        lines = ["Available project datasets:"]
        for name, df in sorted(dataframes.items()):
            lines.append(f"- {name}: {len(df)} rows, {len(df.columns)} columns")
        lines.append("Ask 'Describe <dataset name>' for columns and dtypes.")
        return "\n".join(lines)

    def _build_graph_request_payload(self, message: str, dataframes: dict[str, pd.DataFrame]) -> str:
        dataset_name = self._match_dataset_name(message, dataframes)
        if dataset_name is None and len(dataframes) == 1:
            dataset_name = next(iter(dataframes.keys()))

        if dataset_name is None:
            return self._json_response(
                {
                    "schema_version": "1.0",
                    "action": "error",
                    "message": "Graph request needs a specific dataset.",
                    "error": {
                        "code": "dataset_ambiguous",
                        "detail": "Please include a dataset filename in your prompt.",
                        "available_datasets": sorted(dataframes.keys()),
                    },
                }
            )

        if dataset_name not in dataframes:
            return self._json_response(
                {
                    "schema_version": "1.0",
                    "action": "error",
                    "message": "Dataset not found.",
                    "error": {
                        "code": "dataset_not_found",
                        "detail": f"Dataset '{dataset_name}' does not exist.",
                        "available_datasets": sorted(dataframes.keys()),
                    },
                }
            )

        df = dataframes[dataset_name]
        numeric_cols = [str(col) for col in df.select_dtypes(include="number").columns]
        all_cols = [str(col) for col in df.columns]
        lower = message.lower()

        chart_type = self._detect_chart_type(lower)

        # Validate columns mentioned explicitly in the prompt
        column_validation_error = self._validate_mentioned_columns(message, all_cols)
        if column_validation_error:
            return self._json_response(
                {
                    "schema_version": "1.0",
                    "action": "error",
                    "message": column_validation_error,
                    "error": {
                        "code": "invalid_columns",
                        "detail": column_validation_error,
                        "dataset": dataset_name,
                        "available_columns": sorted(all_cols),
                    },
                }
            )

        # Extract which specific columns to use
        col_assignment = self._extract_columns_from_prompt(message, all_cols, numeric_cols)

        figure_json, error = self._build_figure_json(
            chart_type=chart_type,
            dataset_name=dataset_name,
            df=df,
            all_cols=all_cols,
            numeric_cols=numeric_cols,
            col_assignment=col_assignment,
        )
        if error is not None:
            return self._json_response(
                {
                    "schema_version": "1.0",
                    "action": "error",
                    "message": "Could not build a Plotly figure JSON for this request.",
                    "error": {
                        "code": "figure_build_failed",
                        "detail": error,
                        "dataset": dataset_name,
                        "available_columns": sorted(all_cols),
                        "numeric_columns": sorted(numeric_cols),
                    },
                }
            )

        payload = {
            "schema_version": "1.0",
            "action": "create_graph",
            "message": f"Generated {chart_type} Plotly figure JSON from {dataset_name}.",
            "graph_request": {
                "name": f"AI {chart_type.title()} - {Path(dataset_name).stem}",
                "sources": [dataset_name],
                "intent": {
                    "chart_type": chart_type,
                    "columns": col_assignment,
                    "prompt": message,
                },
                "figure_json": figure_json,
            },
        }
        return self._json_response(payload)

    def _build_figure_json(
        self,
        chart_type: str,
        dataset_name: str,
        df: pd.DataFrame,
        all_cols: list[str],
        numeric_cols: list[str],
        col_assignment: dict,
    ) -> tuple[dict | None, str | None]:
        title = f"{chart_type.title()} from {dataset_name}"
        sample = df.head(2000)

        x_col = col_assignment.get("x")
        y_col = col_assignment.get("y")

        if chart_type == "histogram":
            if x_col is None:
                return None, "Need at least one numeric column for a histogram."
            return (
                {
                    "data": [{"type": "histogram", "x": self._series_values(sample[x_col]), "name": x_col}],
                    "layout": {
                        "template": "plotly_dark",
                        "title": {"text": title},
                        "xaxis": {"title": {"text": x_col}},
                        "yaxis": {"title": {"text": "Count"}},
                    },
                },
                None,
            )

        if chart_type in {"scatter", "line", "bubble", "area"}:
            if x_col is None or y_col is None:
                return None, f"Need at least two columns for a {chart_type} chart."
            mode = {"line": "lines", "area": "lines", "scatter": "markers", "bubble": "markers"}.get(chart_type, "markers")
            trace: dict = {
                "type": "scatter",
                "mode": mode,
                "x": self._series_values(sample[x_col]),
                "y": self._series_values(sample[y_col]),
                "name": f"{y_col} vs {x_col}",
            }
            if chart_type == "area":
                trace["fill"] = "tozeroy"
            layout: dict = {
                "template": "plotly_dark",
                "title": {"text": title},
                "xaxis": {"title": {"text": x_col}},
                "yaxis": {"title": {"text": y_col}},
            }
            return ({"data": [trace], "layout": layout}, None)

        if chart_type == "bar":
            if x_col is None or y_col is None:
                return None, "Need at least two columns for a bar chart."
            return (
                {
                    "data": [{"type": "bar", "x": self._series_values(sample[x_col]), "y": self._series_values(sample[y_col]), "name": f"{y_col} by {x_col}"}],
                    "layout": {
                        "template": "plotly_dark",
                        "title": {"text": title},
                        "xaxis": {"title": {"text": x_col}},
                        "yaxis": {"title": {"text": y_col}},
                    },
                },
                None,
            )

        if chart_type == "box":
            if x_col is None:
                return None, "Need at least one numeric column for a box plot."
            return (
                {
                    "data": [{"type": "box", "y": self._series_values(sample[x_col]), "name": x_col}],
                    "layout": {
                        "template": "plotly_dark",
                        "title": {"text": title},
                        "yaxis": {"title": {"text": x_col}},
                    },
                },
                None,
            )

        if chart_type == "violin":
            if x_col is None:
                return None, "Need at least one numeric column for a violin plot."
            return (
                {
                    "data": [{"type": "violin", "y": self._series_values(sample[x_col]), "name": x_col, "box": {"visible": True}, "meanline": {"visible": True}}],
                    "layout": {
                        "template": "plotly_dark",
                        "title": {"text": title},
                        "yaxis": {"title": {"text": x_col}},
                    },
                },
                None,
            )

        if chart_type == "heatmap":
            if x_col is None or y_col is None:
                return None, "Need at least two numeric columns for a heatmap."
            return (
                {
                    "data": [{"type": "histogram2d", "x": self._series_values(sample[x_col]), "y": self._series_values(sample[y_col])}],
                    "layout": {
                        "template": "plotly_dark",
                        "title": {"text": title},
                        "xaxis": {"title": {"text": x_col}},
                        "yaxis": {"title": {"text": y_col}},
                    },
                },
                None,
            )

        if chart_type == "pie":
            if x_col is None:
                return None, "Need a label column for a pie chart."
            label_values = self._series_values(sample[x_col])
            if y_col:
                value_values = self._series_values(sample[y_col])
            else:
                # Auto-count labels
                counts = sample[x_col].value_counts()
                label_values = list(counts.index.astype(str))
                value_values = list(counts.values)
            return (
                {
                    "data": [{"type": "pie", "labels": label_values, "values": value_values, "name": x_col}],
                    "layout": {"template": "plotly_dark", "title": {"text": title}},
                },
                None,
            )

        if chart_type == "funnel":
            if x_col is None or y_col is None:
                return None, "Need two columns for a funnel chart."
            return (
                {
                    "data": [{"type": "funnel", "x": self._series_values(sample[y_col]), "y": self._series_values(sample[x_col])}],
                    "layout": {"template": "plotly_dark", "title": {"text": title}},
                },
                None,
            )

        if chart_type in {"sunburst", "treemap"}:
            if x_col is None:
                return None, f"Need a label column for a {chart_type} chart."
            counts = sample[x_col].value_counts().head(50)
            return (
                {
                    "data": [{"type": chart_type, "labels": list(counts.index.astype(str)), "values": list(counts.values), "parents": [""] * len(counts)}],
                    "layout": {"template": "plotly_dark", "title": {"text": title}},
                },
                None,
            )

        # Generic fallback: scatter for any unknown type
        if x_col and y_col:
            return (
                {
                    "data": [{"type": "scatter", "mode": "markers", "x": self._series_values(sample[x_col]), "y": self._series_values(sample[y_col]), "name": f"{y_col} vs {x_col}"}],
                    "layout": {
                        "template": "plotly_dark",
                        "title": {"text": f"{title} (rendered as scatter)"},
                        "xaxis": {"title": {"text": x_col}},
                        "yaxis": {"title": {"text": y_col}},
                    },
                },
                None,
            )

        return None, f"Could not determine how to build a '{chart_type}' chart with the available columns."

    def _json_response(self, payload: dict) -> str:
        return json.dumps(payload, indent=2)

    def _series_values(self, series: pd.Series) -> list:
        return [self._normalize_value(value) for value in series.tolist()]

    def _normalize_value(self, value):
        if pd.isna(value):
            return None

        if hasattr(value, "isoformat") and not isinstance(value, (int, float, str, bool)):
            try:
                return value.isoformat()
            except Exception:
                pass

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        return value

    def _describe_dataset(self, name: str, df: pd.DataFrame) -> str:
        columns = [str(col) for col in df.columns]
        dtype_lines = [f"- {col}: {dtype}" for col, dtype in df.dtypes.items()]

        column_preview = ", ".join(columns[:20])
        if len(columns) > 20:
            column_preview += ", ..."

        response_lines = [
            f"Dataset: {name}",
            f"Rows: {len(df)}",
            f"Columns: {len(columns)}",
            f"Column names: {column_preview}",
            "Column dtypes:",
            *dtype_lines,
        ]
        return "\n".join(response_lines)



