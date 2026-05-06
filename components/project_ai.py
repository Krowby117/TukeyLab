from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd


class DatasetCatalogController:
    """Phase 1 controller: list and describe project datasets only."""

    REFUSAL_MESSAGE = (
        "Phase 1 assistant scope is limited to dataset catalog questions. "
        "Try asking: 'What datasets are available?' or 'Describe <dataset name>'."
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

    def _match_dataset_name(self, message: str, dataframes: dict[str, pd.DataFrame]) -> str | None:
        lower = message.lower()

        # Exact filename match first.
        for filename in dataframes:
            if filename.lower() in lower:
                return filename

        # Stem match allows queries like "describe spotify_analysis_dataset".
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

