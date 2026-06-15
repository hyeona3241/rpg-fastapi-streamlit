import streamlit as st
from utils.api import require_login, render_sidebar, request

st.set_page_config(page_title="Battle", layout="wide")
render_sidebar()
st.title("⚔️ Battle")

if not require_login():
    st.stop()

selected = st.session_state.get("selected_character")
if not selected:
    st.info("캐릭터를 먼저 선택해주세요.")
    st.stop()

st.info("몬스터 목록 조회 → 전투 시작 → 장착 스킬 공격 → 보상 지급 순서로 구현할 예정입니다.")
res = request("GET", "/monsters")
if res and res.status_code == 200:
    st.json(res.json())
else:
    st.caption("아직 `/monsters` API가 연결되지 않았습니다.")
