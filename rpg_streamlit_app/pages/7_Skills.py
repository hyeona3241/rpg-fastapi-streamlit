import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Skills", layout="wide")
init_session_state()
render_sidebar()

st.title("✨ Skills")
st.caption("현재 선택 캐릭터가 보유한 기본 스킬을 확인합니다. 장착 기능은 전투 구현 단계에서 추가합니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()

res = request("GET", "/skills/me")
if res is None:
    st.stop()
if res.status_code == 404:
    st.info("선택된 캐릭터가 없습니다. Character 페이지에서 캐릭터를 먼저 선택해주세요.")
    st.stop()
if res.status_code != 200:
    st.error(res.json().get("detail", "스킬 정보를 불러오지 못했습니다."))
    st.stop()

data = res.json()
character = data.get("character", {})
st.subheader(f"{character.get('character_name')}의 보유 스킬")

skills = data.get("skills", [])
if skills:
    st.dataframe(pd.DataFrame(skills), use_container_width=True, hide_index=True)
else:
    st.info("보유 스킬이 없습니다. Skill 마스터 데이터 또는 캐릭터 생성 시 기본 스킬 지급 조건을 확인해주세요.")
