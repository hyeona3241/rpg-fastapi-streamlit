from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import numpy as np

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

from .constants import ATTRIBUTES, EFFECT_COLUMNS, METHODS, METHOD_ALIASES
from .crafting_text import build_item_name_note
from .llm_generator import generate_item_text_openai

MODEL_DIR = Path(__file__).resolve().parent / "models"
ARTIFACT_PATH = MODEL_DIR / "crafting_mlp.joblib"


@dataclass
class CraftingPrediction:
    item_name: str
    item_note: str
    type_effect: str
    effects: dict[str, int]
    attributes: dict[str, float]
    source: str = "fallback"
    text_source: str = "rule"
    llm_debug: dict[str, Any] | None = None


def normalize_method(method: str) -> str:
    return METHOD_ALIASES.get(str(method).strip(), str(method).strip().upper())


def merge_attributes(attrs1: dict[str, Any], attrs2: dict[str, Any]) -> dict[str, float]:
    merged: dict[str, float] = {}
    for attr in ATTRIBUTES:
        v1 = float(attrs1.get(attr, 0) or 0)
        v2 = float(attrs2.get(attr, 0) or 0)
        merged[attr] = round((v1 + v2) / 2.0, 3)
    return merged


def apply_method_modifier(attrs: dict[str, float], method: str) -> dict[str, float]:
    attrs = dict(attrs)
    modifier = {
        "BOIL": ("healing", 0.8),
        "DISTILL": ("toxic", 0.8),
        "BAKE": ("hot", 0.8),
        "COMPRESS": ("dense", 0.8),
        "INFUSE": ("magical", 0.8),
        "MIX": ("stable", 0.4),
    }.get(method)
    if modifier:
        key, bonus = modifier
        attrs[key] = round(float(attrs.get(key, 0) or 0) + bonus, 3)
    return attrs


def build_feature(attrs: dict[str, float], method: str) -> np.ndarray:
    method = normalize_method(method)
    method_onehot = [1.0 if method == m else 0.0 for m in METHODS]
    attr_values = [float(attrs.get(attr, 0) or 0) for attr in ATTRIBUTES]
    return np.array([attr_values + method_onehot], dtype=np.float32)


def _fallback_predict(attrs: dict[str, float], method: str) -> tuple[str, dict[str, int]]:
    attrs = apply_method_modifier(attrs, method)
    healing_score = attrs.get("healing", 0) + attrs.get("pure", 0) + attrs.get("holy", 0)
    poison_score = attrs.get("toxic", 0) + attrs.get("dark", 0)
    attack_score = attrs.get("sharp", 0) + attrs.get("metallic", 0) + attrs.get("hot", 0) + attrs.get("electric", 0)
    defense_score = attrs.get("defensive", 0) + attrs.get("stable", 0) + attrs.get("dense", 0)
    explosive_score = attrs.get("explosive", 0) + attrs.get("unstable", 0)
    scores = {
        "회복형": healing_score,
        "독성형": poison_score,
        "공격형": attack_score,
        "방어형": defense_score,
        "폭발형": explosive_score,
    }
    type_effect = max(scores, key=scores.get)
    base_power = max(3, int(round(max(scores.values()) * 8 + 5)))
    duration = max(3, int(round(attrs.get("viscous", 0) + attrs.get("stable", 0) + 3)))
    effect = {col: 0 for col in EFFECT_COLUMNS}
    effect["duration"] = duration
    if type_effect == "회복형":
        effect["hp"] = min(120, base_power * 2)
        effect["resistance"] = int(attrs.get("holy", 0) + attrs.get("pure", 0))
    elif type_effect == "독성형":
        effect["poison"] = min(60, base_power)
    elif type_effect == "공격형":
        effect["attack"] = min(40, base_power)
        effect["burn"] = int(attrs.get("hot", 0) * 5)
        effect["shock"] = int(attrs.get("electric", 0) * 5)
        effect["freeze"] = int(attrs.get("cold", 0) * 5)
    elif type_effect == "방어형":
        effect["defense"] = min(40, base_power)
        effect["resistance"] = min(40, int(defense_score * 6))
    else:
        effect["explosion_damage"] = min(120, base_power * 2)
        effect["burn"] = int(attrs.get("hot", 0) * 4)
    return type_effect, effect


def _sanitize_prediction(type_effect: str, raw_effects: dict[str, Any]) -> dict[str, int]:
    effects = {col: max(0, int(round(float(raw_effects.get(col, 0) or 0)))) for col in EFFECT_COLUMNS}
    effects["duration"] = min(max(effects.get("duration", 0), 0), 30)
    caps = {
        "hp": 160, "poison": 80, "attack": 60, "defense": 60, "speed": 40,
        "resistance": 60, "burn": 80, "freeze": 80, "shock": 80, "explosion_damage": 180,
    }
    for key, cap in caps.items():
        effects[key] = min(effects.get(key, 0), cap)

    # 타입과 맞지 않는 효과를 약하게 정리해 품질을 안정화한다.
    if type_effect == "회복형":
        for key in ["poison", "attack", "burn", "freeze", "shock", "explosion_damage"]:
            effects[key] = 0
        if effects["hp"] <= 0:
            effects["hp"] = 20
    elif type_effect == "독성형":
        effects["hp"] = 0
        if effects["poison"] <= 0:
            effects["poison"] = 15
    elif type_effect == "공격형":
        effects["hp"] = 0
        if effects["attack"] <= 0 and effects["burn"] + effects["freeze"] + effects["shock"] <= 0:
            effects["attack"] = 12
    elif type_effect == "방어형":
        effects["hp"] = 0
        if effects["defense"] <= 0 and effects["resistance"] <= 0:
            effects["defense"] = 10
    elif type_effect == "폭발형":
        effects["hp"] = 0
        if effects["explosion_damage"] <= 0:
            effects["explosion_damage"] = 25
    return effects


def _load_artifact() -> dict[str, Any] | None:
    if joblib is None or not ARTIFACT_PATH.exists():
        return None
    try:
        return joblib.load(ARTIFACT_PATH)
    except Exception:
        return None


def predict_crafting_result(
    ingredient1_name: str,
    ingredient2_name: str,
    method: str,
    ingredient1_attributes: dict[str, Any],
    ingredient2_attributes: dict[str, Any],
) -> CraftingPrediction:
    method_norm = normalize_method(method)
    merged = apply_method_modifier(merge_attributes(ingredient1_attributes, ingredient2_attributes), method_norm)
    source = "fallback"

    artifact = _load_artifact()
    if artifact:
        try:
            feature = build_feature(merged, method_norm)
            scaler = artifact["scaler"]
            type_model = artifact["type_model"]
            effect_model = artifact["effect_model"]
            label_encoder = artifact["label_encoder"]
            scaled = scaler.transform(feature)
            type_idx = type_model.predict(scaled)[0]
            type_effect = str(label_encoder.inverse_transform([type_idx])[0])
            effect_values = effect_model.predict(scaled)[0]
            raw_effects = {col: effect_values[i] for i, col in enumerate(EFFECT_COLUMNS)}
            effects = _sanitize_prediction(type_effect, raw_effects)
            source = "mlp"
        except Exception:
            type_effect, effects = _fallback_predict(merged, method_norm)
    else:
        type_effect, effects = _fallback_predict(merged, method_norm)

    fallback_name, fallback_note = build_item_name_note(
        ingredient1_name, ingredient2_name, method_norm, type_effect, effects
    )
    llm_text = generate_item_text_openai(
        ingredient1_name=ingredient1_name,
        ingredient2_name=ingredient2_name,
        method=method_norm,
        type_effect=type_effect,
        effects=effects,
        attributes=merged,
        fallback_name=fallback_name,
        fallback_description=fallback_note,
    )
    return CraftingPrediction(
        item_name=llm_text.name,
        item_note=llm_text.description,
        type_effect=type_effect,
        effects=effects,
        attributes=merged,
        source=source,
        text_source=llm_text.source,
        llm_debug=llm_text.debug,
    )


def prediction_to_json(prediction: CraftingPrediction) -> str:
    return json.dumps({
        "item_name": prediction.item_name,
        "item_note": prediction.item_note,
        "type_effect": prediction.type_effect,
        "effects": prediction.effects,
        "attributes": prediction.attributes,
        "source": prediction.source,
        "text_source": prediction.text_source,
        "llm_debug": prediction.llm_debug,
    }, ensure_ascii=False, indent=2)
