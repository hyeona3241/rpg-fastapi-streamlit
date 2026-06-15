import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8001"


def init_session_state() -> None:
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_name": None,
        "role": "USER",
        "cookies": {},
        "selected_character": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def request(method: str, path: str, **kwargs):
    cookies = st.session_state.get("cookies") or {}
    try:
        return requests.request(method, f"{BASE_URL}{path}", cookies=cookies, timeout=5, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("FastAPI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return None
    except requests.exceptions.Timeout:
        st.error("FastAPI 서버 응답 시간이 초과되었습니다.")
        return None


def logout() -> None:
    request("POST", "/logout")
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "USER"
    st.session_state.cookies = {}
    st.session_state.selected_character = None


def require_login() -> bool:
    init_session_state()
    if not st.session_state.logged_in:
        st.warning("로그인이 필요한 기능입니다. Home 화면에서 먼저 로그인해주세요.")
        return False
    return True


def render_sidebar() -> None:
    init_session_state()
    st.sidebar.title("🗡️ My RPG")
    if st.session_state.logged_in:
        st.sidebar.write(f"👤 **{st.session_state.user_id}**")
        st.sidebar.caption(f"Role: {st.session_state.role}")
        selected = st.session_state.get("selected_character")
        if selected:
            st.sidebar.success(f"현재 캐릭터: {selected.get('character_name')} Lv.{selected.get('level')}")
        else:
            st.sidebar.info("현재 선택된 캐릭터가 없습니다.")
        if st.sidebar.button("로그아웃"):
            logout()
            st.rerun()
    else:
        st.sidebar.info("로그인 전")
