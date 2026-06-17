import pandas as pd
import streamlit as st
from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Quest", layout="wide")
init_session_state()
render_sidebar()

st.title("📜 Quest")


def show_error(res, default_msg: str) -> None:
    if res is None:
        st.error(default_msg)
        return
    try:
        st.error(res.json().get("detail", default_msg))
    except Exception:
        st.error(res.text or f"HTTP {res.status_code}: {default_msg}")


def load_available_quests():
    res = request("GET", "/quests")
    if res is None:
        return []
    if res.status_code != 200:
        show_error(res, "퀘스트 목록을 불러오지 못했습니다.")
        return []
    return res.json()


def load_my_quests():
    res = request("GET", "/quests/me")
    if res is None:
        return []
    if res.status_code != 200:
        show_error(res, "내 퀘스트 목록을 불러오지 못했습니다.")
        return []
    return res.json()


if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()

if not st.session_state.get("selected_character_id"):
    st.info("먼저 Character 페이지에서 캐릭터를 선택해주세요.")
    st.stop()

available_tab, my_tab = st.tabs(["수락 가능한 퀘스트", "내 퀘스트"])

with available_tab:
    quests = load_available_quests()
    if not quests:
        st.info("표시할 퀘스트가 없습니다. seed_quest_demo.sql을 실행했는지 확인해주세요.")
    for quest in quests:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            cols[0].subheader(f"{quest['name']} #{quest['quest_id']}")
            cols[1].metric("상태", quest.get("status", "not_accepted"))
            cols[2].metric("EXP 보상", quest.get("reward", {}).get("exp", 0))
            st.write(quest.get("description") or "설명 없음")

            objectives = quest.get("objectives", [])
            if objectives:
                st.markdown("**목표**")
                obj_df = pd.DataFrame(objectives)
                st.dataframe(obj_df, use_container_width=True, hide_index=True)
            else:
                st.caption("목표 데이터가 없습니다.")

            reward_items = quest.get("reward", {}).get("items", [])
            if reward_items:
                st.markdown("**아이템 보상**")
                st.dataframe(pd.DataFrame(reward_items), use_container_width=True, hide_index=True)

            if quest.get("status") == "not_accepted":
                if st.button("퀘스트 수락", key=f"accept_{quest['quest_id']}"):
                    res = request("POST", f"/quests/{quest['quest_id']}/accept")
                    if res is not None and res.status_code == 200:
                        st.success("퀘스트를 수락했습니다.")
                        st.rerun()
                    else:
                        show_error(res, "퀘스트 수락 실패")
            elif quest.get("status") == "active":
                st.info("이미 진행 중인 퀘스트입니다.")
            elif quest.get("status") == "completed":
                st.success("완료한 퀘스트입니다.")

with my_tab:
    quests = load_my_quests()
    if not quests:
        st.info("진행 중인 퀘스트가 없습니다.")
    for quest in quests:
        with st.container(border=True):
            st.subheader(f"{quest['name']} #{quest['quest_id']}")
            st.write(quest.get("description") or "설명 없음")
            status = quest.get("status")
            if status == "active":
                st.info("진행 중")
            elif status == "completed":
                st.success("완료됨")
            else:
                st.caption(status)

            objectives = quest.get("objectives", [])
            for obj in objectives:
                current = int(obj.get("current_count", 0) or 0)
                required = max(1, int(obj.get("required_count", 1) or 1))
                st.write(f"{obj.get('objective_type')} target #{obj.get('target_id')}: {current} / {required}")
                st.progress(max(0.0, min(1.0, current / required)))

            reward = quest.get("reward", {})
            st.write(f"보상 EXP: {reward.get('exp', 0)}")
            if reward.get("items"):
                st.dataframe(pd.DataFrame(reward["items"]), use_container_width=True, hide_index=True)

            if quest.get("can_complete"):
                if st.button("완료하고 보상 받기", key=f"complete_{quest['quest_id']}"):
                    res = request("POST", f"/quests/{quest['quest_id']}/complete")
                    if res is not None and res.status_code == 200:
                        data = res.json()
                        st.success(data.get("message", "퀘스트 완료"))
                        st.json(data.get("reward", {}))
                        st.rerun()
                    else:
                        show_error(res, "퀘스트 완료 실패")
            elif status == "active":
                st.caption("목표를 모두 달성하면 완료할 수 있습니다.")
