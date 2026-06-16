import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request



def safe_detail(res, default_msg: str) -> str:
    if res is None:
        return default_msg
    try:
        return res.json().get("detail", default_msg)
    except Exception:
        return res.text or f"HTTP {res.status_code}: {default_msg}"

st.set_page_config(page_title="Character", layout="wide")
init_session_state()
render_sidebar()

st.title("🛡️ Character")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()


def load_characters():
    res = request("GET", "/characters/me")
    if res is None:
        return []
    if res.status_code != 200:
        st.error(res.json().get("detail", "캐릭터 목록을 불러오지 못했습니다."))
        return []
    return res.json()


def load_specimens():
    res = request("GET", "/specimens")
    if res is None or res.status_code != 200:
        return []
    return res.json()


def refresh_current_character_from_server():
    res = request("GET", "/characters/current")
    if res and res.status_code == 200:
        char = res.json()
        if char:
            st.session_state.selected_character_id = char.get("actor_id")
            st.session_state.selected_character_name = char.get("character_name")
        return char
    return None


tab_list, tab_create, tab_detail = st.tabs(["내 캐릭터", "새 캐릭터 생성", "선택 캐릭터 상세"])

with tab_list:
    st.subheader("내 캐릭터 목록")
    characters = load_characters()
    if characters:
        df = pd.DataFrame(characters)
        show_cols = [c for c in ["actor_id", "character_name", "level", "exp", "active", "is_public"] if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

        st.divider()
        st.write("캐릭터 관리")
        for char in characters:
            cols = st.columns([3, 1, 1, 1])
            label = f"{char['character_name']} (Lv.{char['level']}, ID: {char['actor_id']})"
            if char.get("active"):
                label += " ✅ 선택됨"
            cols[0].write(label)

            if cols[1].button("선택", key=f"select_{char['actor_id']}"):
                res = request("PATCH", f"/characters/{char['actor_id']}/select")
                if res and res.status_code == 200:
                    data = res.json()
                    st.session_state.selected_character_id = data.get("actor_id")
                    st.session_state.selected_character_name = data.get("character_name")
                    st.success("캐릭터를 선택했습니다.")
                    st.rerun()
                elif res is not None:
                    st.error(res.json().get("detail", "캐릭터 선택 실패"))

            visibility_label = "비공개" if char.get("is_public") else "공개"
            if cols[2].button(visibility_label, key=f"visibility_{char['actor_id']}"):
                res = request("PATCH", f"/characters/{char['actor_id']}/visibility", json={"is_public": not char.get("is_public")})
                if res and res.status_code == 200:
                    st.success("공개 여부를 변경했습니다.")
                    st.rerun()
                elif res is not None:
                    st.error(res.json().get("detail", "공개 여부 변경 실패"))

            if cols[3].button("삭제", key=f"delete_{char['actor_id']}"):
                res = request("DELETE", f"/characters/{char['actor_id']}")
                if res and res.status_code == 200:
                    if st.session_state.selected_character_id == char["actor_id"]:
                        st.session_state.selected_character_id = None
                        st.session_state.selected_character_name = None
                    st.success("캐릭터를 삭제했습니다.")
                    st.rerun()
                elif res is not None:
                    st.error(res.json().get("detail", "캐릭터 삭제 실패"))
    else:
        st.info("아직 생성된 캐릭터가 없습니다.")

with tab_create:
    st.subheader("새 캐릭터 생성")
    specimens = load_specimens()
    with st.form("create_character_form"):
        name = st.text_input("캐릭터 이름")

        specimen_payload = []
        if specimens:
            specimen_names = {f"{s['name']} ({s['type']})": s["type"] for s in specimens}
            selected_labels = st.multiselect("종족 선택", options=list(specimen_names.keys()))
            total_percent = 0
            for label in selected_labels:
                percent = st.slider(f"{label} 비율", min_value=0, max_value=100, value=100 if len(selected_labels) == 1 else 0, step=5)
                total_percent += percent
                if percent > 0:
                    specimen_payload.append({"type": specimen_names[label], "fraction": percent / 100})
            st.write(f"총 비율: **{total_percent}%**")
            if selected_labels and total_percent != 100:
                st.warning("종족 비율 합계는 100%여야 합니다.")
        else:
            st.info("종족 데이터가 없으면 기본 종족 HUMAN으로 생성 요청을 보냅니다.")
            specimen_payload = [{"type": "HUMAN", "fraction": 1.0}]

        submitted = st.form_submit_button("생성")

    if submitted:
        if not name.strip():
            st.warning("캐릭터 이름을 입력해주세요.")
        elif not specimen_payload:
            st.warning("종족을 하나 이상 선택하고 비율을 설정해주세요.")
        elif abs(sum(s["fraction"] for s in specimen_payload) - 1.0) > 0.001:
            st.warning("종족 비율 합계가 100%가 아닙니다.")
        else:
            res = request("POST", "/characters", json={"character_name": name, "specimens": specimen_payload})
            if res and res.status_code == 201:
                st.success("캐릭터를 생성했습니다.")
                st.rerun()
            elif res is not None:
                st.error(res.json().get("detail", "캐릭터 생성 실패"))

with tab_detail:
    st.subheader("현재 선택 캐릭터")
    current = refresh_current_character_from_server()
    if not current:
        st.info("내 캐릭터 탭에서 캐릭터를 선택해주세요.")
        st.stop()

    st.metric("캐릭터", current.get("character_name"), f"Lv.{current.get('level')}")
    detail_res = request("GET", f"/characters/{current['actor_id']}")
    if detail_res is None:
        st.stop()
    if detail_res.status_code != 200:
        st.error(safe_detail(detail_res, "상세 정보를 불러오지 못했습니다."))
        st.stop()

    detail = detail_res.json()
    character = detail.get("character", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Actor ID", character.get("actor_id"))
    col2.metric("Level", character.get("level"))
    col3.metric("EXP", character.get("exp"))
    col4.metric("Public", character.get("is_public"))

    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("종족 구성")
        specimens_df = pd.DataFrame(detail.get("specimens", []))
        if not specimens_df.empty:
            specimens_df["fraction"] = specimens_df["fraction"].map(lambda x: f"{x * 100:.0f}%")
            st.dataframe(specimens_df, use_container_width=True, hide_index=True)
        else:
            st.info("종족 정보가 없습니다.")

        st.write("스탯")
        final_stats = detail.get("final_stats") or {}
        if final_stats:
            base = final_stats.get("base", {})
            bonus = final_stats.get("equipment_bonus", {})
            final = final_stats.get("final", {})
            rows = []
            for stat in sorted(set(base) | set(bonus) | set(final)):
                rows.append({
                    "stat": stat,
                    "base": base.get(stat, 0),
                    "equipment_bonus": bonus.get(stat, 0),
                    "final": final.get(stat, 0),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            stats = detail.get("stats", {})
            if stats:
                st.dataframe(pd.DataFrame([{"stat": k, "value": v} for k, v in stats.items()]), use_container_width=True, hide_index=True)
            else:
                st.info("스탯 정보가 없습니다.")

        st.write("장착 장비")
        equipment = detail.get("equipment", [])
        if equipment:
            equip_rows = []
            for eq in equipment:
                equip_rows.append({
                    "slot": eq.get("equipment_part"),
                    "item_id": eq.get("item_id"),
                    "name": eq.get("name"),
                    "bonuses": eq.get("bonuses"),
                })
            st.dataframe(pd.DataFrame(equip_rows), use_container_width=True, hide_index=True)
        else:
            st.info("장착한 장비가 없습니다.")

    with col_right:
        st.write("보유 스킬")
        skills = detail.get("skills", [])
        if skills:
            st.dataframe(pd.DataFrame(skills), use_container_width=True, hide_index=True)
        else:
            st.info("보유 스킬이 없습니다.")