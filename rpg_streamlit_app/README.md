# My RPG Streamlit Client

## 실행 방법

# 프로젝트 폴더로 이동
cd MyRPG

# 가상환경 생성
python -m venv venv

# 활성화 (CMD)
venv\Scripts\activate

# 활성화 (PowerShell)
.\venv\Scripts\Activate.ps1

# 패키지 설치
pip install fastapi uvicorn sqlalchemy pymysql streamlit pandas requests

# 설치 목록 저장
pip freeze > requirements.txt



## 실행 순서

# 1. FastAPI 실행
cd rpg_backend
uvicorn backend_main_v1:app --host 127.0.0.1 --port 8001 --reload

# 2. Streamlit 실행
cd rpg_streamlit_app
streamlit run Home.py


http://localhost:8501 에서 실행 확인

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
