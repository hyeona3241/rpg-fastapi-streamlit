import streamlit as st
from utils.api import require_login, render_sidebar, request

st.set_page_config(page_title="Quest", layout="wide")
render_sidebar()
st.title("📜 Quest")

if not require_login():
    st.stop()

if not st.session_state.get("selected_character"):
    st.info("캐릭터를 먼저 선택해주세요.")
    st.stop()

st.info("NPC 목록 → 퀘스트 수락 → 진행도 확인 → 완료/보상 지급 순서로 구현합니다.")
res = request("GET", "/quests/me")
if res and res.status_code == 200:
    st.json(res.json())
else:
    st.caption("아직 퀘스트 API가 연결되지 않았습니다.")
