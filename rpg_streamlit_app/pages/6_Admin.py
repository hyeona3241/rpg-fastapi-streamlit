import streamlit as st
from utils.api import require_login, render_sidebar, request

st.set_page_config(page_title="Admin", layout="wide")
render_sidebar()
st.title("🛠️ Admin")

if not require_login():
    st.stop()

if st.session_state.get("role") != "ADMIN":
    st.warning("관리자 계정만 접근할 수 있습니다.")
    st.stop()

st.subheader("관리자 대시보드")
for label, endpoint in [("Users", "/admin/users"), ("Characters", "/admin/characters"), ("Items", "/admin/items")]:
    with st.expander(label):
        res = request("GET", endpoint)
        if res and res.status_code == 200:
            st.json(res.json())
        else:
            st.caption(f"{endpoint} API 구현 전입니다.")
