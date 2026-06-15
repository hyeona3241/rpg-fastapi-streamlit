import streamlit as st
from utils.api import require_login, render_sidebar

st.set_page_config(page_title="Crafting", layout="wide")
render_sidebar()
st.title("🧪 Dynamic Crafting")

if not require_login():
    st.stop()

if not st.session_state.get("selected_character"):
    st.info("캐릭터를 먼저 선택해주세요.")
    st.stop()

st.info("인벤토리 재료 선택 → 조합 방법 선택 → 기존 레시피 조회 → 신규 레시피 생성 순서로 구현합니다.")
method = st.selectbox("조합 방법", ["Mix", "Boil", "Bake", "Distill", "Compress", "Infuse"])
st.caption(f"선택한 조합 방법: {method}")
