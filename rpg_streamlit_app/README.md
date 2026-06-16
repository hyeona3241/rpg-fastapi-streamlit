# My RPG Streamlit Client

## 실행 방법

```bash
cd rpg_streamlit_app
streamlit run Home.py
```

FastAPI 서버는 별도 터미널에서 실행합니다.

```bash
uvicorn backend_main_v1:app --reload
```

## 현재 구현 범위

- 로그인 / 회원가입 UI
- 로그인 세션 저장
- 캐릭터 목록 조회
- 캐릭터 생성 UI
- 종족 비율 선택 UI
- 캐릭터 선택 상태 저장
- Inventory / Battle / Crafting / Quest / Admin 페이지 뼈대

## 다음 구현 단계

1. FastAPI `/me`, `/characters/me`, `/characters/{id}/select`, `/specimens` 연결
2. 캐릭터 생성 시 CharacterSpecimen / ActorStat / Inventory 생성
3. 인벤토리 조회 API 구현
4. 전투 / 보상 / 크래프팅 API 구현
