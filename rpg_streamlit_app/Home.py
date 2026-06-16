import streamlit as st
import pandas as pd
from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="My RPG Test Client", layout="wide")
init_session_state()
render_sidebar()

st.title("🗡️ My RPG Test Client")
st.caption("Streamlit Client ↔ FastAPI REST API ↔ MySQL")


def login_view():
    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

    with login_tab:
        with st.form("login_form"):
            user_id = st.text_input("아이디", key="login_user_id")
            password = st.text_input("비밀번호", type="password", key="login_password")
            submitted = st.form_submit_button("로그인")

        if submitted:
            if not user_id or not password:
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")
                return
            res = request("POST", "/login", json={"user_id": user_id, "password": password})
            if res is None:
                return
            if res.status_code == 200:
                data = res.json()
                st.session_state.logged_in = True
                st.session_state.user_id = data.get("user_id", user_id)
                st.session_state.user_name = data.get("user_name")
                st.session_state.role = data.get("role", "USER")
                st.session_state.cookies = res.cookies.get_dict()
                st.success("로그인 성공")
                st.rerun()
            else:
                st.error(res.json().get("detail", "로그인에 실패했습니다."))

    with signup_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새 아이디", key="signup_user_id")
            nickname = st.text_input("닉네임", key="signup_nickname")
            new_pw = st.text_input("비밀번호", type="password", key="signup_password")
            submitted = st.form_submit_button("회원가입")

        if submitted:
            if not new_id or not nickname or not new_pw:
                st.warning("아이디, 닉네임, 비밀번호를 모두 입력해주세요.")
                return
            res = request("POST", "/users", json={
                "user_identifier": new_id,
                "nickname": nickname,
                "password": new_pw,
            })
            if res is None:
                return
            if res.status_code == 201:
                st.success("회원가입 성공! 이제 로그인할 수 있습니다.")
            else:
                st.error(res.json().get("detail", "회원가입에 실패했습니다."))


def dashboard_view():
    st.subheader("메인 대시보드")
    me_res = request("GET", "/me")
    if me_res and me_res.status_code == 200:
        me = me_res.json()
        st.session_state.user_name = me.get("user_name")
        st.session_state.role = me.get("role", "USER")
        col1, col2, col3 = st.columns(3)
        col1.metric("User ID", me.get("user_id"))
        col2.metric("Nickname", me.get("user_name"))
        col3.metric("Role", me.get("role", "USER"))
    else:
        st.info("내 계정 정보 API가 아직 연결되지 않았거나 세션이 만료되었습니다.")

    st.divider()
    st.subheader("계정 비활성화")
    st.warning(
        "계정 비활성화 후에는 로그인할 수 없습니다. 데이터는 보존되며, 동일한 아이디로 재가입할 수 없습니다. "
        "복구는 관리자 계정에서만 가능합니다."
    )
    if st.session_state.get("role") == "ADMIN":
        st.info("관리자 계정은 안전을 위해 비활성화할 수 없습니다.")
    else:
        confirm = st.checkbox("위 내용을 이해했으며, 내 계정을 비활성화합니다.")
        if st.button("내 계정 비활성화", disabled=not confirm, type="secondary"):
            res = request("DELETE", "/users/me")
            if res and res.status_code == 200:
                st.success("계정이 비활성화되었습니다. 다시 로그인하려면 관리자 복구가 필요합니다.")
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.session_state.role = "USER"
                st.session_state.cookies = {}
                st.session_state.selected_character_id = None
                st.session_state.selected_character_name = None
                st.rerun()
            elif res is not None:
                st.error(res.json().get("detail", "계정 비활성화에 실패했습니다."))

    st.divider()
    st.subheader("내 캐릭터 요약")
    res = request("GET", "/characters/me")
    if res is None:
        return
    if res.status_code == 200:
        characters = res.json()
    else:
        # 기존 프로토타입 서버와 호환
        res = request("GET", f"/users/{st.session_state.user_id}/characters")
        characters = res.json() if res and res.status_code == 200 else []

    if characters:
        df = pd.DataFrame(characters)
        columns = [c for c in ["actor_id", "character_name", "level", "exp", "active", "is_public"] if c in df.columns]
        st.dataframe(df[columns], use_container_width=True, hide_index=True)
    else:
        st.info("아직 생성된 캐릭터가 없습니다. Character 페이지에서 캐릭터를 생성하세요.")


if not st.session_state.logged_in:
    login_view()
else:
    dashboard_view()
