from __future__ import annotations

from crafting_ai.crafting_predictor import predict_crafting_result, prediction_to_json

if __name__ == "__main__":
    attrs1 = {"toxic": 1, "plant": 1, "unstable": 1, "dark": 1}
    attrs2 = {"healing": 1, "plant": 1, "stable": 1}
    result = predict_crafting_result("독버섯", "빨간 약초", "MIX", attrs1, attrs2)
    print(prediction_to_json(result))
