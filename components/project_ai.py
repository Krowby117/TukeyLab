from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

try:
    import ollama
except Exception:  # pragma: no cover - optional dependency
    ollama = None


class DatasetCatalogController:
    REFUSAL_MESSAGE = (
        "I can help with project dataset exploration and EDA tasks. "
        "Try: 'What datasets are available?', 'Describe <dataset>', "
        "'Give me an EDA overview for <dataset>', 'Show missing values for <dataset>', "
        "or 'What is the correlation between <col1> and <col2> in <dataset>?'. \n"
    )

    def __init__(
        self,
        get_dataframes: Callable[[], dict[str, pd.DataFrame]],
        use_llm: bool | None = None,
        llm_model: str | None = None,
    ):
        self._get_dataframes = get_dataframes
        env_use_llm = os.getenv("TUKEYLAB_USE_LLM", "1") == "1"
        self._use_llm = env_use_llm if use_llm is None else use_llm
        self._llm_model = llm_model or os.getenv("TUKEYLAB_LLM_MODEL", "phi")
        if ollama is None:
            self._use_llm = False

    def process_message(self, prompt: str, history: list[dict[str, str]] | None = None) -> str:
        message = (prompt or "").strip()
        if not message:
            return "Please enter a question."

        dataframes = self._get_dataframes()
        if not dataframes:
            return "No datasets are loaded in this project yet."

        if self._is_strategy_request(message):
            dataset_name = self._match_dataset_name(message, dataframes)
            if dataset_name is None and len(dataframes) == 1:
                dataset_name = next(iter(dataframes.keys()))
            return self._eda_strategy_response(dataset_name, dataframes)

        if self._is_help_request(message):
            return self._build_help_message(dataframes)

        if self._is_list_request(message):
            return self._build_dataset_catalog(dataframes)

        if self._is_graph_request(message):
            return (
                "I am currently scoped to dataset discussion and EDA reasoning only (no graph creation). "
                "I can still help you decide what to plot and why. "
                "Try: 'What columns should I compare in <dataset>?' or 'What EDA checks should I run first?'."
            )

        if self._use_llm:
            llm_response = self._llm_respond(message, dataframes, history or [])
            if llm_response:
                return llm_response

        return self._process_message_deterministic(message, dataframes)

    def _process_message_deterministic(self, message: str, dataframes: dict[str, pd.DataFrame]) -> str:
        dataset_name = self._match_dataset_name(message, dataframes)
        if dataset_name is None and len(dataframes) == 1:
            dataset_name = next(iter(dataframes.keys()))

        if self._is_strategy_request(message):
            return self._eda_strategy_response(dataset_name, dataframes)

        if self._is_describe_request(message):
            if dataset_name:
                return self._describe_dataset(dataset_name, dataframes[dataset_name])
            return self._dataset_needed_message(dataframes)

        if self._is_overview_request(message):
            if dataset_name:
                return self._eda_overview(dataset_name, dataframes[dataset_name])
            return self._dataset_needed_message(dataframes)

        if self._is_missingness_request(message):
            if dataset_name:
                return self._missingness_report(dataset_name, dataframes[dataset_name])
            return self._dataset_needed_message(dataframes)

        if self._is_summary_request(message):
            if dataset_name:
                return self._summary_stats_report(message, dataset_name, dataframes[dataset_name])
            return self._dataset_needed_message(dataframes)

        if self._is_distribution_request(message):
            if dataset_name:
                return self._distribution_report(message, dataset_name, dataframes[dataset_name])
            return self._dataset_needed_message(dataframes)

        if self._is_correlation_request(message):
            if dataset_name:
                return self._correlation_report(message, dataset_name, dataframes[dataset_name])
            return self._dataset_needed_message(dataframes)

        if dataset_name:
            return self._describe_dataset(dataset_name, dataframes[dataset_name])

        return self.REFUSAL_MESSAGE

    def _is_help_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("help", "what can you do", "how should i", "where do i start"))

    def _is_list_request(self, message: str) -> bool:
        lower = message.lower()
        return any(
            text in lower
            for text in (
                "what datasets",
                "which datasets",
                "list datasets",
                "available datasets",
                "data sources",
                "what files",
                "tell me about the datasets",
                "datasets i have loaded",
                "datasets loaded",
            )
        )

    def _is_describe_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("describe", "about dataset", "columns", "schema", "dtypes"))

    def _is_graph_request(self, message: str) -> bool:
        lower = message.lower()
        return any(
            k in lower
            for k in (
                "create graph",
                "create a graph",
                "make graph",
                "make a graph",
                "plot",
                "chart",
                "scatter",
                "histogram",
                "bar chart",
                "line chart",
                "heatmap",
                "box plot",
                "violin",
                "pie",
            )
        )

    def _is_overview_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("eda overview", "overview", "quick summary", "profile dataset"))

    def _is_missingness_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("missing", "null", "na values", "empty values"))

    def _is_summary_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("summary stats", "statistics", "mean", "median", "std", "describe()"))

    def _is_distribution_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("distribution", "value counts", "top values", "frequency"))

    def _is_correlation_request(self, message: str) -> bool:
        lower = message.lower()
        return any(k in lower for k in ("correlation", "corr", "relationship", "compare"))

    def _is_strategy_request(self, message: str) -> bool:
        lower = message.lower()
        return any(
            k in lower
            for k in (
                "what eda steps",
                "eda steps should i take",
                "what should i do next",
                "help me compare",
                "good way to compare",
                "what should i compare",
                "what next",
            )
        )

    def _match_dataset_name(self, message: str, dataframes: dict[str, pd.DataFrame]) -> str | None:
        lower = message.lower()

        # Exact match first (full filename appears in message)
        for filename in dataframes:
            if filename.lower() in lower:
                return filename

        # Stem match (filename without extension)
        stem_matches = []
        for filename in dataframes:
            stem = Path(filename).stem.lower()
            if stem and stem in lower:
                stem_matches.append(filename)

        if len(stem_matches) == 1:
            return stem_matches[0]
        if len(stem_matches) > 1:
            # If multiple stem matches, try partial keyword matching
            best_match = self._find_best_partial_match(message, stem_matches)
            if best_match:
                return best_match

        # Partial keyword matching (individual keywords from message match parts of filename)
        partial_matches = self._find_best_partial_match(message, list(dataframes.keys()))
        if partial_matches:
            return partial_matches

        return None

    def _find_best_partial_match(self, message: str, filenames: list[str]) -> str | None:
        """Find the best matching filename based on keyword overlap scoring."""
        lower_msg = message.lower()
        # Extract keywords from message (remove common words and short tokens)
        keywords = [
            token.strip(".,!?;:") for token in lower_msg.split()
            if len(token.strip(".,!?;:")) > 2 and token.strip(".,!?;:") not in {
                "the", "and", "for", "with", "from", "that", "this", "can", "have",
                "data", "dataset", "csv", "file", "show", "give", "tell", "what",
                "which", "where", "how", "why", "when", "should", "would", "could"
            }
        ]

        if not keywords:
            return None

        scored_matches: list[tuple[str, int]] = []
        for filename in filenames:
            filename_lower = filename.lower()
            stem = Path(filename).stem.lower()
            full_name = (stem + " " + filename_lower).lower()

            score = 0
            for keyword in keywords:
                if keyword in full_name:
                    score += len(keyword)  # Longer keyword matches score higher
                    if keyword in stem:
                        score += 2  # Boost if keyword is in the stem

            if score > 0:
                scored_matches.append((filename, score))

        if not scored_matches:
            return None

        # Return the highest-scoring match
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[0][0]

    def _dataset_needed_message(self, dataframes: dict[str, pd.DataFrame]) -> str:
        names = ", ".join(sorted(dataframes.keys()))
        return (
            "Please include a dataset name so I can run that EDA task. "
            f"Available datasets: {names}"
        )

    def _build_help_message(self, dataframes: dict[str, pd.DataFrame]) -> str:
        examples = [
            "- What datasets are available?",
            "- Describe spotify_analysis_dataset.csv",
            "- Give me an EDA overview for dirty_cafe_sales.csv",
            "- Show missing values in dirty_cafe_sales.csv",
            "- Summary statistics for spotify_analysis_dataset.csv",
            "- Correlation between tempo and valence in spotify_analysis_dataset.csv",
            "- Distribution of genre in spotify_analysis_dataset.csv",
        ]
        return (
            "I support iterative, dataset-grounded EDA conversations so you can reason through patterns and refine your understanding.\n"
            "I can help with:\n"
            "- dataset inventory and schema checks\n"
            "- EDA overviews\n"
            "- missingness analysis\n"
            "- summary statistics\n"
            "- basic distribution and correlation checks\n\n"
            "Prompt ideas:\n"
            + "\n".join(examples)
            + "\n\n"
            + f"Loaded datasets: {', '.join(sorted(dataframes.keys()))}"
        )

    def _eda_strategy_response(self, dataset_name: str | None, dataframes: dict[str, pd.DataFrame]) -> str:
        if dataset_name is None:
            return (
                "Great question. A practical next EDA sequence is: (1) dataset overview, (2) missingness check, "
                "(3) summary stats, (4) distributions, (5) pairwise correlations for numeric features, and "
                "(6) inspect surprising outliers. Include a dataset name and I can tailor this to your data.\n"
                f"Loaded datasets: {', '.join(sorted(dataframes.keys()))}"
            )

        df = dataframes[dataset_name]
        numeric_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(exclude="number").columns)
        pair_hint = ""
        if len(numeric_cols) >= 2:
            pair_hint = f"Start by comparing {numeric_cols[0]} vs {numeric_cols[1]} and checking their correlation."

        return (
            f"EDA next steps for {dataset_name}:\n"
            "1) Check shape, dtypes, and obvious quality issues.\n"
            "2) Review missing values by column and decide imputation/drop rules.\n"
            "3) Run summary stats on numeric features (mean/median/std/min/max).\n"
            "4) Inspect distributions (numeric) and value counts (categorical).\n"
            "5) Compare related features and investigate outliers.\n"
            f"Numeric columns: {len(numeric_cols)}, Categorical columns: {len(cat_cols)}. {pair_hint}"
        )

    def _llm_respond(
        self,
        message: str,
        dataframes: dict[str, pd.DataFrame],
        history: list[dict[str, str]],
    ) -> str | None:
        if ollama is None:
            return None

        context = self._build_dataset_context(dataframes)
        system_prompt = (
            "You are a project-scoped data assistant.\n"
            "Only answer questions about the provided datasets and EDA tasks.\n"
            "Never answer with external/world knowledge.\n"
            "If the user asks outside scope, set in_scope to false and provide a short refusal.\n"
            "Return valid JSON only with keys: in_scope (boolean), answer (string)."
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self._history_to_messages(history))
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Dataset context:\n{context}\n\n"
                    f"User question:\n{message}\n\n"
                    "Remember: answer only from provided datasets and EDA scope."
                ),
            }
        )

        try:
            response = ollama.chat(model=self._llm_model, messages=messages)
        except Exception:
            return None

        content = response.get("message", {}).get("content", "").strip()
        if not content:
            return None

        parsed = self._parse_llm_json(content)
        if parsed is None:
            return None

        if not parsed.get("in_scope", False):
            return self.REFUSAL_MESSAGE

        answer = str(parsed.get("answer", "")).strip()
        return answer or None

    def _parse_llm_json(self, content: str) -> dict | None:
        try:
            return json.loads(content)
        except Exception:
            pass

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = content[start : end + 1]
            try:
                return json.loads(snippet)
            except Exception:
                return None
        return None

    def _history_to_messages(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        if not history:
            return []

        trimmed = history[-12:]
        out: list[dict[str, str]] = []
        for msg in trimmed:
            role = msg.get("role", "").strip().lower()
            if role not in {"user", "assistant"}:
                continue
            content = str(msg.get("content", "")).strip()
            if not content:
                continue
            out.append({"role": role, "content": content})
        return out

    def _build_dataset_context(self, dataframes: dict[str, pd.DataFrame]) -> str:
        lines: list[str] = []
        for name, df in sorted(dataframes.items()):
            numeric_cols = list(df.select_dtypes(include="number").columns)
            non_numeric_cols = list(df.select_dtypes(exclude="number").columns)
            missing = df.isna().sum().sort_values(ascending=False)
            missing = missing[missing > 0]

            lines.append(f"Dataset: {name}")
            lines.append(f"- Shape: {len(df)} rows x {len(df.columns)} columns")
            lines.append(f"- Columns: {', '.join([str(c) for c in list(df.columns)[:25]])}")
            lines.append(f"- Numeric columns ({len(numeric_cols)}): {', '.join([str(c) for c in numeric_cols[:12]])}")
            lines.append(f"- Non-numeric columns ({len(non_numeric_cols)}): {', '.join([str(c) for c in non_numeric_cols[:12]])}")

            if not missing.empty:
                top_missing = ", ".join([f"{idx}:{int(val)}" for idx, val in missing.head(6).items()])
                lines.append(f"- Missing (top): {top_missing}")
            else:
                lines.append("- Missing: none")

            if numeric_cols:
                stats_df = df[numeric_cols[:6]].describe().transpose()
                for col in stats_df.index:
                    row = stats_df.loc[col]
                    lines.append(
                        f"  - {col}: mean={row['mean']:.3f}, std={row['std']:.3f}, min={row['min']:.3f}, max={row['max']:.3f}"
                    )

            lines.append("")

        return "\n".join(lines).strip()

    def _build_dataset_catalog(self, dataframes: dict[str, pd.DataFrame]) -> str:
        lines = ["Available project datasets:"]
        for name, df in sorted(dataframes.items()):
            lines.append(f"- {name}: {len(df)} rows, {len(df.columns)} columns")
        lines.append("Ask 'Describe <dataset>' or 'Give me an EDA overview for <dataset>'.")
        return "\n".join(lines)

    def _describe_dataset(self, name: str, df: pd.DataFrame) -> str:
        columns = [str(col) for col in df.columns]
        numeric_cols = list(df.select_dtypes(include="number").columns)
        categorical_cols = list(df.select_dtypes(exclude="number").columns)
        dtype_lines = [f"- {col}: {dtype}" for col, dtype in df.dtypes.items()]

        column_preview = ", ".join(columns[:20])
        if len(columns) > 20:
            column_preview += ", ..."

        response_lines = [
            f"Dataset: {name}",
            f"Rows: {len(df)}",
            f"Columns: {len(columns)}",
            f"Numeric columns: {len(numeric_cols)}",
            f"Non-numeric columns: {len(categorical_cols)}",
            f"Column names: {column_preview}",
            "Column dtypes:",
            *dtype_lines,
            "",
            "Suggested next step: Ask for an 'EDA overview' or 'missing values' for this dataset.",
        ]
        return "\n".join(response_lines)

    def _eda_overview(self, name: str, df: pd.DataFrame) -> str:
        numeric_cols = list(df.select_dtypes(include="number").columns)
        categorical_cols = list(df.select_dtypes(exclude="number").columns)
        missing_total = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        lines = [
            f"EDA overview for {name}:",
            f"- Shape: {df.shape[0]} rows x {df.shape[1]} columns",
            f"- Numeric columns: {len(numeric_cols)}",
            f"- Non-numeric columns: {len(categorical_cols)}",
            f"- Missing values (total cells): {missing_total}",
            f"- Duplicate rows: {duplicate_rows}",
        ]

        if numeric_cols:
            num_preview = ", ".join([str(c) for c in numeric_cols[:8]])
            lines.append(f"- Numeric preview columns: {num_preview}")

        if categorical_cols:
            cat_preview = ", ".join([str(c) for c in categorical_cols[:8]])
            lines.append(f"- Categorical preview columns: {cat_preview}")

        lines.extend(
            [
                "",
                "Try next:",
                "- 'Show missing values in this dataset'",
                "- 'Summary statistics for this dataset'",
                "- 'Correlation in this dataset'",
            ]
        )

        return "\n".join(lines)

    def _missingness_report(self, name: str, df: pd.DataFrame) -> str:
        missing = df.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False)

        if missing.empty:
            return f"Missingness report for {name}: no missing values found."

        total_rows = len(df)
        lines = [f"Missingness report for {name} (top columns):"]
        for col, cnt in missing.head(15).items():
            pct = (float(cnt) / total_rows) * 100 if total_rows else 0.0
            lines.append(f"- {col}: {int(cnt)} missing ({pct:.2f}%)")

        if len(missing) > 15:
            lines.append(f"- ... and {len(missing) - 15} more columns with missing data")

        return "\n".join(lines)

    def _summary_stats_report(self, message: str, name: str, df: pd.DataFrame) -> str:
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty:
            return f"Summary statistics for {name}: no numeric columns available."

        selected_cols = self._match_columns_in_prompt(message, list(numeric_df.columns))
        if selected_cols:
            numeric_df = numeric_df[selected_cols]

        desc = numeric_df.describe().transpose()
        lines = [f"Summary statistics for {name}:"]
        for col in desc.index[:10]:
            row = desc.loc[col]
            lines.append(
                f"- {col}: mean={row['mean']:.3f}, median={numeric_df[col].median():.3f}, "
                f"std={row['std']:.3f}, min={row['min']:.3f}, max={row['max']:.3f}"
            )

        if len(desc.index) > 10:
            lines.append(f"- ... and {len(desc.index) - 10} more numeric columns")

        return "\n".join(lines)

    def _distribution_report(self, message: str, name: str, df: pd.DataFrame) -> str:
        col = self._pick_best_column_from_prompt(message, list(df.columns))
        if col is None:
            return f"Distribution request for {name}: could not determine a column name from your prompt."

        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna()
            if clean.empty:
                return f"Distribution of {col} in {name}: column has only missing values."
            q1 = clean.quantile(0.25)
            q2 = clean.quantile(0.50)
            q3 = clean.quantile(0.75)
            return (
                f"Distribution of {col} in {name}:\n"
                f"- count={int(clean.shape[0])}\n"
                f"- mean={clean.mean():.3f}\n"
                f"- std={clean.std():.3f}\n"
                f"- min={clean.min():.3f}, q1={q1:.3f}, median={q2:.3f}, q3={q3:.3f}, max={clean.max():.3f}"
            )

        vc = s.astype(str).value_counts(dropna=False)
        lines = [f"Distribution of {col} in {name} (top categories):"]
        for label, cnt in vc.head(12).items():
            lines.append(f"- {label}: {int(cnt)}")
        if len(vc) > 12:
            lines.append(f"- ... and {len(vc) - 12} more categories")
        return "\n".join(lines)

    def _correlation_report(self, message: str, name: str, df: pd.DataFrame) -> str:
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.shape[1] < 2:
            return f"Correlation analysis for {name}: need at least two numeric columns."

        matched_cols = self._match_columns_in_prompt(message, list(numeric_df.columns))
        if len(matched_cols) >= 2:
            c1, c2 = matched_cols[0], matched_cols[1]
            corr_val = numeric_df[c1].corr(numeric_df[c2])
            if pd.isna(corr_val):
                return f"Correlation between {c1} and {c2} in {name} is undefined (insufficient paired values)."
            return f"Correlation between {c1} and {c2} in {name}: {corr_val:.4f}"

        corr = numeric_df.corr().abs()
        mask = corr.where(~np.tril(np.ones(corr.shape)).astype(bool))
        pairs = mask.stack().sort_values(ascending=False)

        if pairs.empty:
            return f"Correlation analysis for {name}: no valid numeric pairs found."

        lines = [f"Top absolute correlations in {name}:"]
        for (c1, c2), val in pairs.head(10).items():
            lines.append(f"- {c1} vs {c2}: {val:.4f}")

        return "\n".join(lines)

    def _match_columns_in_prompt(self, message: str, columns: list[str]) -> list[str]:
        lower_msg = message.lower()
        matches: list[str] = []
        for col in sorted(columns, key=len, reverse=True):
            if str(col).lower() in lower_msg:
                matches.append(str(col))
        # Preserve order of mention by scanning prompt tokens.
        ordered: list[str] = []
        for token in lower_msg.replace(",", " ").replace(".", " ").split():
            for m in matches:
                if token == m.lower() and m not in ordered:
                    ordered.append(m)
        # Include matched columns that may be multi-word after token pass.
        for m in matches:
            if m not in ordered:
                ordered.append(m)
        return ordered

    def _pick_best_column_from_prompt(self, message: str, columns: list[str]) -> str | None:
        matches = self._match_columns_in_prompt(message, columns)
        if matches:
            return matches[0]
        if columns:
            return str(columns[0])
        return None
