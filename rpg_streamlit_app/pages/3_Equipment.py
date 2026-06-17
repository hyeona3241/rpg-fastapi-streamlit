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

st.set_page_config(page_title="Equipment", layout="wide")
init_session_state()
render_sidebar()

st.title("🧰 Equipment")
st.caption("현재 선택 캐릭터의 장비를 장착/해제하고, 장비 보너스가 반영된 최종 스탯을 확인합니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()


def load_equipment():
    res = request("GET", "/equipment/me")
    if res is None:
        return None
    if res.status_code == 404:
        st.info("선택된 캐릭터가 없습니다. Character 페이지에서 캐릭터를 먼저 선택해주세요.")
        return None
    if res.status_code != 200:
        st.error(safe_detail(res, "장비 정보를 불러오지 못했습니다."))
        return None
    return res.json()


data = load_equipment()
if not data:
    st.stop()

character = data.get("character", {})
st.subheader(f"{character.get('character_name')}의 장비")
st.caption(f"Character ID: {character.get('actor_id')} / Level: {character.get('level')}")

equipment = data.get("equipment", [])
available_items = data.get("available_items", [])
stats = data.get("stats", {})

col_left, col_right = st.columns([1, 1])

with col_left:
    st.write("### 현재 장착 장비")
    if equipment:
        rows = []
        for eq in equipment:
            rows.append({
                "slot": eq.get("equipment_part"),
                "item_id": eq.get("item_id"),
                "name": eq.get("name"),
                "required_level": eq.get("required_level"),
                "rarity": eq.get("rarity"),
                "bonuses": eq.get("bonuses"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("장착한 장비가 없습니다.")

    st.write("### 장비 해제")
    if equipment:
        slot_options = [eq.get("equipment_part") for eq in equipment]
        selected_slot = st.selectbox("해제할 슬롯", slot_options)
        if st.button("장비 해제", type="secondary", use_container_width=True):
            res = request("POST", "/equipment/unequip", json={"equipment_part": selected_slot})
            if res and res.status_code == 200:
                st.success(res.json().get("message", "장비를 해제했습니다."))
                st.rerun()
            elif res is not None:
                st.error(safe_detail(res, "장비 해제 실패"))
    else:
        st.caption("해제할 장비가 없습니다.")

with col_right:
    st.write("### 최종 스탯")
    base = stats.get("base", {})
    bonus = stats.get("equipment_bonus", {})
    final = stats.get("final", {})
    stat_rows = []
    for stat in sorted(set(base) | set(bonus) | set(final)):
        stat_rows.append({
            "stat": stat,
            "base": base.get(stat, 0),
            "equipment_bonus": bonus.get(stat, 0),
            "final": final.get(stat, 0),
        })
    if stat_rows:
        st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)
    else:
        st.info("스탯 정보가 없습니다.")

st.divider()
st.write("### 인벤토리의 장착 가능 아이템")

if not available_items:
    st.info("인벤토리에 장비 아이템이 없습니다. Admin 페이지에서 장비 아이템을 지급할 수 있습니다.")
    st.stop()

available_df = pd.DataFrame(available_items)
show_cols = [
    c for c in [
        "item_id", "name", "quantity", "type", "sub_type", "equipment_part",
        "equipped", "equipped_part", "required_level", "rarity", "bonuses", "description",
    ] if c in available_df.columns
]
st.dataframe(available_df[show_cols], use_container_width=True, hide_index=True)

st.write("### 장비 장착")
item_options = {
    f"[{item['item_id']}] {item['name']} x{item.get('quantity', 0)} / slot={item.get('equipment_part') or item.get('sub_type')}": item
    for item in available_items
}
selected_label = st.selectbox("장착할 아이템", list(item_options.keys()))
selected_item = item_options[selected_label]

slot_default = selected_item.get("equipment_part") or selected_item.get("sub_type") or "weapon"
slot = st.text_input("장착 슬롯", value=str(slot_default).lower())

occupied_slots = {eq.get("equipment_part"): eq for eq in equipment}

if selected_item.get("equipped"):
    st.success(f"현재 {selected_item.get('equipped_part')} 슬롯에 장착 중인 아이템입니다.")
    can_equip = False
else:
    can_equip = True
    if slot in occupied_slots:
        current = occupied_slots[slot]
        st.warning(f"{slot} 슬롯에는 현재 '{current.get('name')}' 장비가 장착되어 있습니다. 장착하면 해당 슬롯의 장비가 교체됩니다.")

if st.button("장착 / 교체", type="primary", use_container_width=True, disabled=not can_equip):
    res = request("POST", "/equipment/equip", json={"item_id": int(selected_item["item_id"]), "equipment_part": slot})
    if res and res.status_code == 200:
        st.session_state["equipment_message"] = res.json().get("message", "장비를 장착했습니다.")
        st.rerun()
    elif res is not None:
        st.error(safe_detail(res, "장비 장착 실패"))

if "equipment_message" in st.session_state:
    st.success(st.session_state.pop("equipment_message"))

st.info("전투 중에는 장비 장착/해제가 제한됩니다. 장비 보너스는 캐릭터 상세와 전투 데미지 계산에 반영됩니다.")