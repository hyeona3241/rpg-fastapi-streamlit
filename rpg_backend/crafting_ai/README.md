# AI Crafting Module

Colab 노트북에 있던 크래프팅 AI를 FastAPI에서 재사용하기 위한 로컬 모듈입니다.

## 구조

```text
crafting_ai/
├── train_crafting_model.py      # 데이터셋으로 MLP 모델 학습
├── crafting_predictor.py        # FastAPI에서 호출하는 예측 함수
├── crafting_text.py             # 이름/설명 생성 및 후처리
├── constants.py                 # 속성/효과 컬럼 정의
└── models/
    ├── crafting_mlp.joblib      # 학습 후 생성
    └── metrics.json             # 학습 성능 기록
```

## 학습

```bash
cd rpg_backend
python -m crafting_ai.train_crafting_model --dataset ../../generated_crafting_dataset_rule_llm_2000.xlsx
```

## 예측 테스트

```bash
cd rpg_backend
python -m crafting_ai.test_predictor
```

모델 파일이 없거나 로드 실패 시 규칙 기반 fallback으로 동작합니다.
FastAPI에서는 기존 레시피가 없을 때만 `predict_crafting_result()`를 호출합니다.
