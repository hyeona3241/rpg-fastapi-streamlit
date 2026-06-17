import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Recipe Book", layout="wide")
init_session_state()
render_sidebar()

st.title("📚 레시피 도감")
st.caption("DB에 저장된 크래프팅 레시피를 확인합니다. 같은 조합은 AI를 다시 호출하지 않고 이 레시피를 재사용합니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()


def api_error(res, default_msg: str) -> str:
    try:
        return res.json().get("detail", default_msg)
    except Exception:
        return res.text or default_msg

res = request("GET", "/crafting/recipes")
if res is None:
    st.stop()
if res.status_code != 200:
    st.error(api_error(res, "레시피 목록을 불러오지 못했습니다."))
    st.stop()

recipes = res.json()
if not recipes:
    st.info("아직 등록된 레시피가 없습니다. Crafting 페이지에서 새 조합을 제작해보세요.")
    st.stop()

col1, col2, col3 = st.columns([2, 1.2, 1.2])
search = col1.text_input("검색", placeholder="재료명 또는 결과 아이템명")
methods = sorted({r.get("method") for r in recipes if r.get("method")})
method_filter = col2.selectbox("조합 방법", ["전체"] + methods)
ai_filter = col3.selectbox("생성 방식", ["전체", "AI 생성", "수동/기존"])

filtered = []
for r in recipes:
    text = " ".join([
        str(r.get("ingredient1_name", "")),
        str(r.get("ingredient2_name", "")),
        str(r.get("result_item_name", "")),
        str(r.get("method", "")),
    ]).lower()
    if search.strip() and search.strip().lower() not in text:
        continue
    if method_filter != "전체" and r.get("method") != method_filter:
        continue
    if ai_filter == "AI 생성" and not r.get("created_by_ai"):
        continue
    if ai_filter == "수동/기존" and r.get("created_by_ai"):
        continue
    filtered.append(r)

rows = []
for r in filtered:
    effect = r.get("effect") or {}
    rows.append({
        "recipe_id": r.get("recipe_id"),
        "재료1": r.get("ingredient1_name"),
        "재료2": r.get("ingredient2_name"),
        "방법": r.get("method"),
        "결과": r.get("result_item_name"),
        "효과": effect.get("type_effect"),
        "AI 생성": r.get("created_by_ai"),
        "생성일": r.get("created_at"),
    })

st.write(f"총 {len(filtered)}개 레시피")
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.subheader("레시피 상세")
options = {f"#{r.get('recipe_id')} {r.get('ingredient1_name')} + {r.get('ingredient2_name')} / {r.get('method')} → {r.get('result_item_name')}": r for r in filtered}
if options:
    selected = st.selectbox("상세 확인할 레시피", list(options.keys()))
    recipe = options[selected]
    c1, c2, c3 = st.columns(3)
    c1.metric("Recipe ID", recipe.get("recipe_id"))
    c2.metric("Result Item", recipe.get("result_item_id"))
    c3.metric("Created by AI", str(recipe.get("created_by_ai")))
    st.write("결과 설명")
    st.info(recipe.get("result_description") or "설명 없음")
    st.write("효과")
    st.json(recipe.get("effect") or {})
