import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Admin", layout="wide")
init_session_state()
render_sidebar()

st.title("🛠️ Admin")
st.caption("관리자 전용 계정 관리 및 테스트 아이템 지급 화면")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()

if st.session_state.get("role") != "ADMIN":
    st.error("관리자 권한이 필요합니다.")
    st.stop()


def api_error(res, default_msg):
    try:
        return res.json().get("detail", default_msg)
    except Exception:
        return default_msg


tab_users, tab_grant = st.tabs(["계정 관리", "아이템 지급"])

with tab_users:
    st.subheader("계정 검색 / 필터링")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        keyword = st.text_input("아이디 또는 닉네임 검색", placeholder="예: admin, test", key="user_keyword")
    with col2:
        active_filter_label = st.selectbox("계정 상태", ["전체", "활성", "비활성"], key="user_active_filter")
    with col3:
        role_filter = st.selectbox("권한", ["ALL", "USER", "ADMIN"], key="user_role_filter")

    params = {}
    if keyword.strip():
        params["keyword"] = keyword.strip()
    if active_filter_label == "활성":
        params["active"] = True
    elif active_filter_label == "비활성":
        params["active"] = False
    if role_filter != "ALL":
        params["role"] = role_filter

    res = request("GET", "/admin/users", params=params)
    if res is None:
        st.stop()
    if res.status_code != 200:
        st.error(api_error(res, "유저 목록을 불러오지 못했습니다."))
        st.stop()

    users = res.json()
    if not users:
        st.info("조건에 맞는 계정이 없습니다.")
    else:
        df = pd.DataFrame(users)
        display_df = df.rename(columns={
            "user_id": "아이디",
            "user_name": "닉네임",
            "role": "권한",
            "active": "활성 상태",
            "character_count": "캐릭터 수",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("계정별 활성화 / 비활성화")
        for user in users:
            with st.container(border=True):
                cols = st.columns([2, 2, 1, 1, 2])
                cols[0].write(f"**{user['user_id']}**")
                cols[1].write(user["user_name"])
                cols[2].write(user["role"])
                cols[3].write("활성" if user["active"] else "비활성")

                if user["role"] == "ADMIN":
                    cols[4].button("관리자 보호", disabled=True, key=f"admin_protect_{user['user_id']}")
                elif user["active"]:
                    if cols[4].button("비활성화", key=f"deactivate_{user['user_id']}"):
                        update_res = request("PATCH", f"/admin/users/{user['user_id']}/active", json={"active": False})
                        if update_res and update_res.status_code == 200:
                            st.success(f"{user['user_id']} 계정을 비활성화했습니다.")
                            st.rerun()
                        elif update_res is not None:
                            st.error(api_error(update_res, "계정 비활성화 실패"))
                else:
                    if cols[4].button("복구", type="primary", key=f"restore_{user['user_id']}"):
                        update_res = request("PATCH", f"/admin/users/{user['user_id']}/active", json={"active": True})
                        if update_res and update_res.status_code == 200:
                            st.success(f"{user['user_id']} 계정을 복구했습니다.")
                            st.rerun()
                        elif update_res is not None:
                            st.error(api_error(update_res, "계정 복구 실패"))

with tab_grant:
    st.subheader("캐릭터에게 테스트 아이템 지급")
    st.caption("전투/퀘스트 구현 전에도 인벤토리와 크래프팅 테스트를 할 수 있도록 관리자 지급 기능을 제공합니다.")

    char_keyword = st.text_input("캐릭터/유저 검색", placeholder="캐릭터명, 유저 ID, 닉네임", key="grant_char_keyword")
    char_params = {}
    if char_keyword.strip():
        char_params["keyword"] = char_keyword.strip()

    char_res = request("GET", "/admin/characters", params=char_params)
    item_res = request("GET", "/admin/items")

    if char_res is None or item_res is None:
        st.stop()
    if char_res.status_code != 200:
        st.error(api_error(char_res, "캐릭터 목록을 불러오지 못했습니다."))
        st.stop()
    if item_res.status_code != 200:
        st.error(api_error(item_res, "아이템 목록을 불러오지 못했습니다."))
        st.stop()

    characters = char_res.json()
    items = item_res.json()

    if not characters:
        st.info("지급할 캐릭터가 없습니다.")
        st.stop()
    if not items:
        st.info("지급할 아이템이 없습니다. Item 테이블에 테스트 데이터를 먼저 넣어주세요.")
        st.stop()

    col_c, col_i, col_q = st.columns([2, 2, 1])
    with col_c:
        char_options = {
            f"[{c['actor_id']}] {c['character_name']} / {c['user_id']} ({c['user_name']})": c
            for c in characters
        }
        selected_char_label = st.selectbox("캐릭터 선택", list(char_options.keys()))
        selected_char = char_options[selected_char_label]

    with col_i:
        item_type_filter = st.selectbox("아이템 타입 필터", ["ALL", "material", "consumable", "equipment", "others"], key="grant_item_type")
        filtered_items = [i for i in items if item_type_filter == "ALL" or i.get("type") == item_type_filter]
        item_options = {
            f"[{i['id']}] {i['name']} ({i['type']}/{i.get('sub_type')})": i
            for i in filtered_items
        }
        if not item_options:
            st.warning("해당 타입의 아이템이 없습니다.")
            st.stop()
        selected_item_label = st.selectbox("아이템 선택", list(item_options.keys()))
        selected_item = item_options[selected_item_label]

    with col_q:
        quantity = st.number_input("수량", min_value=1, value=1, step=1)

    st.write("#### 지급 정보 확인")
    st.json({
        "character": selected_char,
        "item": selected_item,
        "quantity": int(quantity),
    })

    if st.button("선택 캐릭터에게 아이템 지급", type="primary", use_container_width=True):
        grant_res = request(
            "POST",
            f"/admin/characters/{selected_char['actor_id']}/items",
            json={"item_id": selected_item["id"], "quantity": int(quantity)},
        )
        if grant_res and grant_res.status_code == 200:
            data = grant_res.json()
            st.success(f"{selected_char['character_name']}에게 {data.get('item_name')} {data.get('quantity_added')}개를 지급했습니다.")
        elif grant_res is not None:
            st.error(api_error(grant_res, "아이템 지급 실패"))
