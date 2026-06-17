from __future__ import annotations

import argparse
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import make_pipeline

from crafting_ai.constants import ATTRIBUTES, EFFECT_COLUMNS, METHODS, METHOD_ALIASES


def normalize_method(value: str) -> str:
    return METHOD_ALIASES.get(str(value).strip(), str(value).strip().upper())


def build_features(df: pd.DataFrame) -> np.ndarray:
    method = df["method"].map(normalize_method)
    attr_values = df[ATTRIBUTES].fillna(0).astype(float).to_numpy()
    method_onehot = np.array([[1.0 if m == method.iloc[i] else 0.0 for m in METHODS] for i in range(len(df))])
    return np.concatenate([attr_values, method_onehot], axis=1).astype(np.float32)


def train(dataset_path: Path, output_dir: Path, test_size: float = 0.2, random_state: int = 42) -> None:
    df = pd.read_excel(dataset_path)
    missing = [c for c in ["method", "type_effect", *ATTRIBUTES, *EFFECT_COLUMNS] if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}")

    x = build_features(df)
    y_type = df["type_effect"].astype(str)
    y_effect = df[EFFECT_COLUMNS].fillna(0).astype(float).to_numpy()
    label_encoder = LabelEncoder()
    y_type_encoded = label_encoder.fit_transform(y_type)

    x_train, x_test, yt_train, yt_test, ye_train, ye_test = train_test_split(
        x, y_type_encoded, y_effect, test_size=test_size, random_state=random_state, stratify=y_type_encoded
    )

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    type_model = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        max_iter=700,
        random_state=random_state,
        early_stopping=True,
        n_iter_no_change=30,
    )
    type_model.fit(x_train_scaled, yt_train)

    effect_model = MLPRegressor(
        hidden_layer_sizes=(96, 64),
        activation="relu",
        max_iter=900,
        random_state=random_state,
        early_stopping=True,
        n_iter_no_change=35,
    )
    effect_model.fit(x_train_scaled, ye_train)

    type_pred = type_model.predict(x_test_scaled)
    effect_pred = effect_model.predict(x_test_scaled)
    metrics = {
        "type_accuracy": float(accuracy_score(yt_test, type_pred)),
        "effect_mae": float(mean_absolute_error(ye_test, effect_pred)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "labels": label_encoder.classes_.tolist(),
        "feature_columns": [*ATTRIBUTES, *[f"method_{m}" for m in METHODS]],
        "effect_columns": EFFECT_COLUMNS,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "scaler": scaler,
        "type_model": type_model,
        "effect_model": effect_model,
        "label_encoder": label_encoder,
        "attributes": ATTRIBUTES,
        "methods": METHODS,
        "effect_columns": EFFECT_COLUMNS,
        "metrics": metrics,
    }
    joblib.dump(artifact, output_dir / "crafting_mlp.joblib")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Saved: {output_dir / 'crafting_mlp.joblib'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="generated_crafting_dataset_rule_llm_2000.xlsx")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent / "models"))
    args = parser.parse_args()
    train(Path(args.dataset), Path(args.output_dir))


if __name__ == "__main__":
    main()
