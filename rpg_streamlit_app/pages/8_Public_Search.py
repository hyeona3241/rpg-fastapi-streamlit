import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Public Character Search", layout="wide")
init_session_state()
render_sidebar()

st.title("🔎 공개 캐릭터 검색")
st.caption("공개 상태로 설정된 캐릭터만 검색할 수 있습니다. 비공개 캐릭터의 인벤토리, 장비, 세부 스탯은 표시하지 않습니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()


def api_error(res, default_msg: str) -> str:
    try:
        return res.json().get("detail", default_msg)
    except Exception:
        return res.text or default_msg


def load_jobs():
    res = request("GET", "/jobs")
    if res is None or res.status_code != 200:
        return []
    return res.json()


def load_specimens():
    res = request("GET", "/specimens")
    if res is None or res.status_code != 200:
        return []
    return res.json()

jobs = load_jobs()
specimens = load_specimens()

with st.form("public_search_form"):
    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
    name = c1.text_input("캐릭터 이름", placeholder="이름 일부 입력")

    job_options = {"전체": None}
    job_options.update({f"{j['name']} ({j['type']})": j["type"] for j in jobs})
    job_label = c2.selectbox("직업", list(job_options.keys()))

    specimen_options = {"전체": None}
    specimen_options.update({f"{s['name']} ({s['type']})": s["type"] for s in specimens})
    specimen_label = c3.selectbox("종족", list(specimen_options.keys()))

    min_level = c4.number_input("최소 Lv", min_value=1, value=1, step=1)
    max_level = st.number_input("최대 Lv", min_value=1, value=999, step=1)
    submitted = st.form_submit_button("검색", type="primary")

params = {}
if submitted or "last_public_search" not in st.session_state:
    if name.strip():
        params["name"] = name.strip()
    if job_options[job_label]:
        params["job_type"] = job_options[job_label]
    if specimen_options[specimen_label]:
        params["specimen_type"] = specimen_options[specimen_label]
    if min_level:
        params["min_level"] = int(min_level)
    if max_level:
        params["max_level"] = int(max_level)

    res = request("GET", "/characters/public/search", params=params)
    if res is None:
        st.stop()
    if res.status_code != 200:
        st.error(api_error(res, "공개 캐릭터 검색에 실패했습니다."))
        st.stop()
    st.session_state.last_public_search = res.json()

results = st.session_state.get("last_public_search", [])
st.divider()
st.subheader("검색 결과")

if not results:
    st.info("조건에 맞는 공개 캐릭터가 없습니다.")
else:
    rows = []
    for row in results:
        specimen_text = ", ".join([
            f"{s.get('type')} {float(s.get('fraction', 0)) * 100:.0f}%"
            for s in row.get("specimens", [])
        ])
        rows.append({
            "actor_id": row.get("actor_id"),
            "name": row.get("character_name"),
            "level": row.get("level"),
            "job": row.get("job_name") or row.get("job_type"),
            "specimens": specimen_text,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.write("상세 보기")
    options = {f"[{r['actor_id']}] {r['character_name']} Lv.{r['level']}": r for r in results}
    selected = st.selectbox("공개 캐릭터 선택", list(options.keys()))
    char_id = options[selected]["actor_id"]
    if st.button("공개 상세 조회"):
        res = request("GET", f"/characters/{char_id}")
        if res and res.status_code == 200:
            detail = res.json()
            st.json({
                "character": detail.get("character"),
                "jobs": detail.get("jobs"),
                "specimens": detail.get("specimens"),
            })
        elif res is not None:
            st.error(api_error(res, "상세 조회 실패"))
