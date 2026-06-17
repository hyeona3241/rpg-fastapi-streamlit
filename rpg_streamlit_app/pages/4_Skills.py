import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Skills", layout="wide")
init_session_state()
render_sidebar()

st.title("✨ Skills")
st.caption("보유 스킬을 확인하고 전투에서 사용할 스킬을 최대 3개까지 장착합니다.")

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
st.subheader(f"{character.get('character_name')}의 스킬")

skills = data.get("skills", [])
equipped = data.get("equipped", [])

left, right = st.columns([1, 1])

with left:
    st.markdown("### 장착 스킬")
    if equipped:
        eq_df = pd.DataFrame(equipped)[["slot_no", "id", "name", "mp_cost", "cooldown_sec"]]
        eq_df.columns = ["슬롯", "스킬 ID", "스킬명", "MP", "쿨다운"]
        st.dataframe(eq_df, use_container_width=True, hide_index=True)
    else:
        st.info("장착된 스킬이 없습니다.")

    st.markdown("#### 슬롯 해제")
    slot_to_remove = st.selectbox("해제할 슬롯", [1, 2, 3], key="unequip_slot")
    if st.button("선택 슬롯 해제"):
        remove_res = request("POST", "/skills/unequip", json={"slot_no": slot_to_remove})
        if remove_res is not None and remove_res.status_code == 200:
            st.success(remove_res.json().get("message", "해제했습니다."))
            st.rerun()
        elif remove_res is not None:
            st.error(remove_res.json().get("detail", "해제 실패"))

with right:
    st.markdown("### 스킬 장착")
    if not skills:
        st.info("보유 스킬이 없습니다.")
    else:
        skill_options = {f"[{s['id']}] {s['name']} / MP {s['mp_cost']} / CD {s['cooldown_sec']}": s["id"] for s in skills}
        selected_skill_label = st.selectbox("장착할 스킬", list(skill_options.keys()))
        selected_slot = st.selectbox("장착 슬롯", [1, 2, 3], key="equip_slot")
        if st.button("스킬 장착"):
            equip_res = request(
                "POST",
                "/skills/equip",
                json={"skill_id": skill_options[selected_skill_label], "slot_no": selected_slot},
            )
            if equip_res is not None and equip_res.status_code == 200:
                st.success(equip_res.json().get("message", "장착했습니다."))
                st.rerun()
            elif equip_res is not None:
                st.error(equip_res.json().get("detail", "장착 실패"))

st.divider()
st.markdown("### 보유 스킬 전체")
if skills:
    df = pd.DataFrame(skills)
    display_cols = ["id", "name", "description", "mp_cost", "cooldown_sec", "skill_level", "equipped", "slot_no"]
    df = df[[c for c in display_cols if c in df.columns]]
    df.columns = ["스킬 ID", "스킬명", "설명", "MP", "쿨다운", "숙련도", "장착 여부", "슬롯"][: len(df.columns)]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("보유 스킬이 없습니다. 캐릭터 생성 시 기본 스킬 지급 또는 스킬 마스터 데이터를 확인해주세요.")
