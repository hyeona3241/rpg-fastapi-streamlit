import streamlit as st
import pandas as pd
from utils.api import require_login, render_sidebar, request

st.set_page_config(page_title="Character", layout="wide")
render_sidebar()
st.title("🛡️ Character")

if not require_login():
    st.stop()


def get_characters():
    res = request("GET", "/characters/me")
    if res and res.status_code == 200:
        return res.json()
    # 기존 프로토타입 서버 호환용 fallback
    res = request("GET", f"/users/{st.session_state.user_id}/characters")
    if res and res.status_code == 200:
        return res.json()
    return []


def get_specimens():
    res = request("GET", "/specimens")
    if res and res.status_code == 200:
        return res.json()
    # API 구현 전에도 UI 확인 가능하도록 fallback
    return [
        {"type": "HUMAN", "name": "Human"},
        {"type": "ELF", "name": "Elf"},
        {"type": "ORC", "name": "Orc"},
    ]

list_tab, create_tab, detail_tab = st.tabs(["내 캐릭터", "새 캐릭터 생성", "선택 캐릭터 상세"])

with list_tab:
    st.subheader("내 캐릭터 목록")
    characters = get_characters()
    if characters:
        df = pd.DataFrame(characters)
        columns = [c for c in ["actor_id", "character_name", "level", "exp", "active", "is_public"] if c in df.columns]
        st.dataframe(df[columns], use_container_width=True, hide_index=True)

        options = {f"{c['character_name']} (ID: {c['actor_id']})": c for c in characters}
        selected_label = st.selectbox("현재 플레이할 캐릭터 선택", list(options.keys()))
        selected_char = options[selected_label]
        if st.button("이 캐릭터 선택"):
            res = request("PATCH", f"/characters/{selected_char['actor_id']}/select")
            if res and res.status_code == 200:
                st.session_state.selected_character = res.json()
                st.success("캐릭터를 선택했습니다.")
                st.rerun()
            else:
                # 서버 API 미구현 시 UI 상태만 임시 반영
                st.session_state.selected_character = selected_char
                st.warning("선택 API가 아직 없어서 Streamlit 세션에만 임시 저장했습니다.")
    else:
        st.info("생성된 캐릭터가 없습니다.")

with create_tab:
    st.subheader("새 캐릭터 생성")
    specimens = get_specimens()
    specimen_labels = {f"{s.get('name', s.get('type'))} ({s.get('type')})": s.get("type") for s in specimens}

    with st.form("create_character_form"):
        character_name = st.text_input("캐릭터 이름")
        selected_specimen_labels = st.multiselect("종족 선택", list(specimen_labels.keys()))
        fractions = {}
        total = 0
        for label in selected_specimen_labels:
            value = st.slider(f"{label} 비율", 0, 100, 100 if len(selected_specimen_labels) == 1 else 0, 5)
            fractions[specimen_labels[label]] = value / 100
            total += value
        st.write(f"현재 비율 합계: **{total}%**")
        submitted = st.form_submit_button("캐릭터 생성")

    if submitted:
        if not character_name:
            st.warning("캐릭터 이름을 입력해주세요.")
        elif not selected_specimen_labels:
            st.warning("종족을 하나 이상 선택해주세요.")
        elif total != 100:
            st.warning("종족 비율 합계가 100%여야 합니다.")
        else:
            payload = {
                "character_name": character_name,
                "specimens": [
                    {"type": specimen_type, "fraction": fraction}
                    for specimen_type, fraction in fractions.items()
                    if fraction > 0
                ],
            }
            res = request("POST", "/characters", json=payload)
            if res and res.status_code == 201:
                st.success("캐릭터가 생성되었습니다.")
                st.rerun()
            else:
                # 기존 프로토타입 서버 호환
                res = request("POST", f"/users/{st.session_state.user_id}/characters", json={"character_name": character_name})
                if res and res.status_code == 201:
                    st.success("캐릭터가 생성되었습니다. 종족 정보는 새 API 구현 후 저장됩니다.")
                    st.rerun()
                elif res:
                    st.error(res.json().get("detail", "캐릭터 생성 실패"))

with detail_tab:
    st.subheader("선택 캐릭터 상세")
    selected = st.session_state.get("selected_character")
    if not selected:
        st.info("먼저 캐릭터를 선택해주세요.")
    else:
        st.json(selected)
        detail_res = request("GET", f"/characters/{selected['actor_id']}")
        if detail_res and detail_res.status_code == 200:
            st.write("### 서버 상세 정보")
            st.json(detail_res.json())
