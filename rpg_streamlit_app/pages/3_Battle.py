import streamlit as st
from utils.api import init_session_state, render_sidebar

st.set_page_config(page_title="Coming Soon", layout="wide")
init_session_state()
render_sidebar()

st.title("준비 중")
if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
else:
    st.info("이 페이지는 다음 단계에서 구현합니다.")
