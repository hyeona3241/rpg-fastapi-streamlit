import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Crafting", layout="wide")
init_session_state()
render_sidebar()

st.title("🧪 Crafting")
st.caption("인벤토리의 재료 2개와 조합 방법을 선택해 새 아이템을 제작합니다. 기존 레시피가 있으면 저장된 결과를 재사용합니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()


def api_error(res, default_msg: str) -> str:
    try:
        return res.json().get("detail", default_msg)
    except Exception:
        return res.text or default_msg


def load_methods():
    res = request("GET", "/crafting/methods")
    if res is None:
        return []
    if res.status_code != 200:
        st.error(api_error(res, "조합 방법을 불러오지 못했습니다."))
        return []
    return res.json()


def load_materials():
    res = request("GET", "/crafting/materials")
    if res is None:
        return None
    if res.status_code != 200:
        st.error(api_error(res, "크래프팅 재료를 불러오지 못했습니다."))
        return None
    return res.json()


def load_recipes():
    res = request("GET", "/crafting/recipes")
    if res is None or res.status_code != 200:
        return []
    return res.json()


def load_history():
    res = request("GET", "/crafting/history")
    if res is None or res.status_code != 200:
        return []
    return res.json()


tab_craft, tab_recipes, tab_history = st.tabs(["제작", "레시피 도감", "제작 기록"])

with tab_craft:
    methods = load_methods()
    material_data = load_materials()
    if material_data is None:
        st.stop()

    character = material_data.get("character", {})
    materials = material_data.get("materials", [])
    st.subheader("현재 캐릭터")
    st.write(f"**{character.get('character_name', 'Unknown')}** / ID: {character.get('actor_id')}")

    if not materials:
        st.info("조합 가능한 재료가 없습니다. Admin 페이지에서 material 아이템을 지급하거나 전투/퀘스트 보상으로 재료를 획득해보세요.")
        st.stop()
    if len(materials) < 2 and materials[0].get("quantity", 0) < 2:
        st.warning("재료가 2개 이상 필요합니다. 같은 재료를 두 번 사용할 경우 수량이 2개 이상이어야 합니다.")

    col1, col2, col3 = st.columns([2, 2, 1.4])
    item_options = {
        f"[{m['item_id']}] {m['name']} x{m['quantity']} ({m.get('type')}/{m.get('sub_type')})": m
        for m in materials
    }
    method_options = {f"{m['method']} - {m.get('description') or ''}": m for m in methods}

    with col1:
        label1 = st.selectbox("재료 1", list(item_options.keys()), key="craft_ing1")
        ingredient1 = item_options[label1]
    with col2:
        label2 = st.selectbox("재료 2", list(item_options.keys()), key="craft_ing2")
        ingredient2 = item_options[label2]
    with col3:
        if not method_options:
            st.error("조합 방법 데이터가 없습니다. DB 패치 SQL을 실행해주세요.")
            st.stop()
        method_label = st.selectbox("조합 방법", list(method_options.keys()), key="craft_method")
        method = method_options[method_label]["method"]

    st.divider()
    st.subheader("선택 재료 속성")
    attr_rows = []
    for material in [ingredient1, ingredient2]:
        attrs = material.get("attributes", {}) or {}
        strong = {k: v for k, v in attrs.items() if float(v or 0) > 0}
        attr_rows.append({
            "item_id": material["item_id"],
            "name": material["name"],
            "quantity": material["quantity"],
            "attributes": ", ".join([f"{k}:{v:g}" for k, v in strong.items()]) or "속성 없음",
        })
    st.dataframe(pd.DataFrame(attr_rows), use_container_width=True, hide_index=True)

    same_item = ingredient1["item_id"] == ingredient2["item_id"]
    if same_item and ingredient1.get("quantity", 0) < 2:
        st.error("같은 재료를 2개 조합하려면 수량이 2개 이상 필요합니다.")
        disabled = True
    else:
        disabled = False

    if st.button("제작하기", type="primary", use_container_width=True, disabled=disabled):
        craft_res = request(
            "POST",
            "/crafting/craft",
            json={
                "ingredient1_id": ingredient1["item_id"],
                "ingredient2_id": ingredient2["item_id"],
                "method": method,
            },
        )
        if craft_res is None:
            st.stop()
        if craft_res.status_code == 200:
            st.session_state.last_crafting_result = craft_res.json()
        else:
            st.error(api_error(craft_res, "크래프팅 실패"))

    data = st.session_state.get("last_crafting_result")
    if data:
        st.divider()
        if data.get("created_new_recipe"):
            st.success(data.get("message", "새 AI 조합 생성 완료"))
        else:
            st.info(data.get("message", "기존 레시피로 제작했습니다."))

        result = data.get("result_item", {})
        st.write("### 결과 아이템")
        c1, c2, c3 = st.columns(3)
        c1.metric("Item ID", result.get("item_id", "-"))
        c2.metric("이름", result.get("name", "-"))
        c3.metric("현재 수량", result.get("current_quantity", "-"))
        st.caption(result.get("description", ""))

        recipe = data.get("recipe", {})
        effect = recipe.get("effect")
        if effect:
            st.write("### 최종 저장 효과")
            st.json(effect)

        ai_debug = data.get("ai_debug")
        if ai_debug:
            with st.expander("🧠 AI 생성 과정 보기", expanded=bool(data.get("created_new_recipe"))):
                if ai_debug.get("recipe_source") == "cached_recipe":
                    st.info(ai_debug.get("message", "DB에 저장된 기존 레시피를 사용했습니다."))
                else:
                    st.write("#### 1. 입력 재료 속성")
                    ingredients_debug = ai_debug.get("ingredients", [])
                    for idx, ing in enumerate(ingredients_debug, start=1):
                        st.write(f"**재료 {idx}: [{ing.get('item_id')}] {ing.get('name')}**")
                        st.json(ing.get("attributes", {}))

                    st.write("#### 2. 조합 방법 및 AI 입력 특징")
                    st.write(f"Method: `{ai_debug.get('method')}`")
                    st.write("MLP 입력에 사용된 최종 속성 벡터")
                    st.json(ai_debug.get("final_input_attributes", {}))

                    st.write("#### 3. MLP / Fallback 예측 결과")
                    st.write(f"Model source: `{ai_debug.get('model_source')}`")
                    if ai_debug.get("ai_error"):
                        st.warning(f"AI 모델 호출 실패로 fallback 사용: {ai_debug.get('ai_error')}")
                    st.write(f"Predicted type_effect: **{ai_debug.get('predicted_type_effect')}**")

                    st.write("#### 4. 후처리된 효과 수치")
                    st.json(ai_debug.get("post_processed_effects", {}))

                    st.write("#### 5. LLM / 이름·설명 생성")
                    st.write(f"Text source: `{ai_debug.get('text_source', 'unknown')}`")
                    llm_debug = ai_debug.get("llm_debug") or {}
                    if llm_debug:
                        if llm_debug.get("used"):
                            st.success(f"OpenAI 호출 사용: {llm_debug.get('model')}")
                        else:
                            st.warning(llm_debug.get("error", "OpenAI를 사용하지 않고 규칙 기반 fallback을 사용했습니다."))
                        st.write("**LLM 디버그 정보**")
                        safe_debug = dict(llm_debug)
                        # API 키나 민감 정보는 응답에 포함하지 않는다.
                        st.json(safe_debug)

                    st.write("#### 6. 생성된 이름/설명")
                    st.json(ai_debug.get("generated_text", {}))

        if data.get("quest_updates"):
            st.info(f"퀘스트 진행도 {len(data['quest_updates'])}건이 갱신되었습니다.")

        if st.button("결과 패널 닫기"):
            st.session_state.last_crafting_result = None
            st.rerun()

with tab_recipes:
    st.subheader("등록된 레시피")
    recipes = load_recipes()
    if recipes:
        flat = []
        for r in recipes:
            effect = r.get("effect") or {}
            flat.append({
                "recipe_id": r.get("recipe_id"),
                "ingredient1": r.get("ingredient1_name"),
                "ingredient2": r.get("ingredient2_name"),
                "method": r.get("method"),
                "result": r.get("result_item_name"),
                "type_effect": effect.get("type_effect"),
                "hp": effect.get("hp"),
                "poison": effect.get("poison"),
                "attack": effect.get("attack"),
                "defense": effect.get("defense"),
                "created_by_ai": r.get("created_by_ai"),
            })
        st.dataframe(pd.DataFrame(flat), use_container_width=True, hide_index=True)
    else:
        st.info("아직 등록된 레시피가 없습니다.")

with tab_history:
    st.subheader("내 제작 기록")
    history = load_history()
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    else:
        st.info("아직 제작 기록이 없습니다.")
