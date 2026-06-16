import os
from typing import Any

import requests
import streamlit as st

# FastAPI server URL. If your backend runs on another port, set RPG_API_URL env var.
BASE_URL = os.getenv("RPG_API_URL", "http://127.0.0.1:8001")


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "logged_in": False,
        "user_id": None,
        "user_name": None,
        "role": "USER",
        "cookies": {},
        "selected_character_id": None,
        "selected_character_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def request(method: str, endpoint: str, **kwargs):
    """Small wrapper around requests that automatically sends session cookies."""
    url = f"{BASE_URL}{endpoint}"
    cookies = kwargs.pop("cookies", st.session_state.get("cookies") or {})
    try:
        return requests.request(method, url, cookies=cookies, timeout=10, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error(f"FastAPI 서버에 연결할 수 없습니다: {BASE_URL}")
    except requests.exceptions.Timeout:
        st.error("FastAPI 서버 응답 시간이 초과되었습니다.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"요청 중 오류가 발생했습니다: {exc}")
    return None


def logout() -> None:
    try:
        request("POST", "/logout")
    finally:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.role = "USER"
        st.session_state.cookies = {}
        st.session_state.selected_character_id = None
        st.session_state.selected_character_name = None
        st.rerun()


def render_sidebar() -> None:
    st.sidebar.title("🗡️ My RPG")
    st.sidebar.caption(f"API: {BASE_URL}")
    if st.session_state.get("logged_in"):
        st.sidebar.divider()
        st.sidebar.write(f"👤 **{st.session_state.get('user_id')}**")
        if st.session_state.get("user_name"):
            st.sidebar.write(f"닉네임: {st.session_state.get('user_name')}")
        st.sidebar.write(f"권한: `{st.session_state.get('role', 'USER')}`")
        if st.session_state.get("selected_character_name"):
            st.sidebar.success(f"현재 캐릭터: {st.session_state.selected_character_name}")
        else:
            st.sidebar.info("현재 선택 캐릭터 없음")
        st.sidebar.button("로그아웃", on_click=logout)
    else:
        st.sidebar.info("로그인이 필요합니다.")
