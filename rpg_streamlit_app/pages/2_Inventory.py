import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Inventory", layout="wide")
init_session_state()
render_sidebar()

st.title("🎒 Inventory")
st.caption("현재 선택 캐릭터의 인벤토리 아이템을 확인하고, 소비/버리기 기능을 테스트합니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()


def load_inventory():
    res = request("GET", "/inventory")
    if res is None:
        return None
    if res.status_code == 404:
        st.info("선택된 캐릭터가 없습니다. Character 페이지에서 캐릭터를 먼저 선택해주세요.")
        return None
    if res.status_code != 200:
        st.error(res.json().get("detail", "인벤토리를 불러오지 못했습니다."))
        return None
    return res.json()


data = load_inventory()
if not data:
    st.stop()

character = data.get("character", {})
st.subheader(f"{character.get('character_name')}의 인벤토리")
st.caption(f"Character ID: {character.get('actor_id')} / Level: {character.get('level')} / EXP: {character.get('exp')}")

inventories = data.get("inventories", [])
if not inventories:
    st.info("생성된 인벤토리가 없습니다. 캐릭터 생성 로직에서 기본 인벤토리 생성 여부를 확인해주세요.")
    st.stop()

all_items = []
for inv in inventories:
    for item in inv.get("items", []):
        item = dict(item)
        item["inventory_id"] = inv.get("inventory_id")
        all_items.append(item)

summary_cols = st.columns(3)
summary_cols[0].metric("Inventory Count", len(inventories))
summary_cols[1].metric("Item Types", len(all_items))
summary_cols[2].metric("Total Quantity", sum(int(i.get("quantity", 0)) for i in all_items))

st.divider()

for inv in inventories:
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Inventory ID", inv.get("inventory_id"))
        col2.metric("Type", inv.get("type"))
        col3.metric("Capacity", f"{inv.get('used_slots', 0)} / {inv.get('capacity')}")

        items = inv.get("items", [])
        if items:
            df = pd.DataFrame(items)
            show_cols = [
                c for c in [
                    "item_id", "name", "type", "sub_type", "quantity", "rarity",
                    "equipment_part", "required_level", "is_generated", "description",
                ] if c in df.columns
            ]
            st.dataframe(df[show_cols], use_container_width=True, hide_index=True)
        else:
            st.info("아직 보유 아이템이 없습니다. Admin 페이지에서 테스트 아이템을 지급할 수 있습니다.")

st.divider()
st.subheader("아이템 상세 / 사용 / 버리기")

if not all_items:
    st.info("보유 아이템이 없어 사용할 수 있는 기능이 없습니다.")
    st.stop()

item_options = {
    f"[{item['item_id']}] {item['name']} x{item['quantity']} ({item['type']})": item
    for item in all_items
}
selected_label = st.selectbox("아이템 선택", list(item_options.keys()))
selected_item = item_options[selected_label]

col_left, col_right = st.columns([2, 1])
with col_left:
    st.write("### 상세 정보")
    detail_rows = [
        {"항목": "ID", "값": selected_item.get("item_id")},
        {"항목": "이름", "값": selected_item.get("name")},
        {"항목": "타입", "값": selected_item.get("type")},
        {"항목": "서브 타입", "값": selected_item.get("sub_type")},
        {"항목": "수량", "값": selected_item.get("quantity")},
        {"항목": "희귀도", "값": selected_item.get("rarity")},
        {"항목": "장비 부위", "값": selected_item.get("equipment_part")},
        {"항목": "요구 레벨", "값": selected_item.get("required_level")},
        {"항목": "AI 생성 아이템", "값": selected_item.get("is_generated")},
        {"항목": "설명", "값": selected_item.get("description")},
    ]
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

with col_right:
    st.write("### 작업")
    max_qty = max(1, int(selected_item.get("quantity", 1)))
    qty = st.number_input("수량", min_value=1, max_value=max_qty, value=1, step=1)

    item_type = str(selected_item.get("type", "")).lower()
    if item_type == "consumable":
        if st.button("사용", type="primary", use_container_width=True):
            res = request("POST", f"/inventory/items/{selected_item['item_id']}/use", json={"quantity": int(qty)})
            if res and res.status_code == 200:
                st.success(res.json().get("message", "아이템을 사용했습니다."))
                st.rerun()
            elif res is not None:
                st.error(res.json().get("detail", "아이템 사용 실패"))
    else:
        st.caption("소비 아이템만 사용할 수 있습니다.")

    if st.button("버리기", type="secondary", use_container_width=True):
        res = request("POST", f"/inventory/items/{selected_item['item_id']}/discard", json={"quantity": int(qty)})
        if res and res.status_code == 200:
            st.success(res.json().get("message", "아이템을 버렸습니다."))
            st.rerun()
        elif res is not None:
            st.error(res.json().get("detail", "아이템 버리기 실패"))

st.info("아이템 획득은 이후 몬스터 전투/퀘스트 보상과 연결할 예정이며, 지금은 Admin 페이지에서 테스트 지급할 수 있습니다.")
