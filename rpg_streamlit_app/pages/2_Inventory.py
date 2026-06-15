import streamlit as st
import pandas as pd
from utils.api import require_login, render_sidebar, request

st.set_page_config(page_title="Inventory", layout="wide")
render_sidebar()
st.title("🎒 Inventory")

if not require_login():
    st.stop()

selected = st.session_state.get("selected_character")
if not selected:
    st.info("캐릭터를 먼저 선택해주세요.")
    st.stop()

st.subheader(f"{selected.get('character_name')}의 인벤토리")
res = request("GET", "/inventory")
if res and res.status_code == 200:
    items = res.json()
    if items:
        st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
    else:
        st.info("인벤토리에 아이템이 없습니다.")
else:
    st.info("인벤토리 API 구현 전입니다. 다음 단계에서 `/inventory`를 연결합니다.")
