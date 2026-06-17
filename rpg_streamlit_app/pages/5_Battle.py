import pandas as pd
import streamlit as st

from utils.api import init_session_state, render_sidebar, request

st.set_page_config(page_title="Battle", layout="wide")
init_session_state()
render_sidebar()

st.title("⚔️ Battle")
st.caption("몬스터를 선택하고, 장착한 스킬로만 턴제 전투를 진행합니다.")

if not st.session_state.logged_in:
    st.warning("로그인 후 사용할 수 있습니다.")
    st.stop()

if "battle_id" not in st.session_state:
    st.session_state.battle_id = None
if "last_battle_log" not in st.session_state:
    st.session_state.last_battle_log = []

# Current skills
skill_res = request("GET", "/skills/me")
if skill_res is None:
    st.stop()
if skill_res.status_code == 404:
    st.info("선택된 캐릭터가 없습니다. Character 페이지에서 캐릭터를 먼저 선택해주세요.")
    st.stop()
if skill_res.status_code != 200:
    st.error(skill_res.json().get("detail", "스킬 정보를 불러오지 못했습니다."))
    st.stop()

skill_data = skill_res.json()
equipped = skill_data.get("equipped", [])

left, right = st.columns([1, 1])

with left:
    st.subheader("몬스터 선택")
    monster_res = request("GET", "/monsters")
    if monster_res is None:
        st.stop()
    if monster_res.status_code != 200:
        st.error(monster_res.json().get("detail", "몬스터 목록을 불러오지 못했습니다."))
        st.stop()

    monsters = monster_res.json()
    if not monsters:
        st.warning("등록된 몬스터가 없습니다. populate SQL의 Monster 데이터를 확인해주세요.")
        st.stop()

    monster_options = {
        f"[{m['actor_id']}] {m['name']} Lv.{m.get('level', 1)} / HP {m['hp']} / ATK {m['atk']} / DEF {m['def']}": m["actor_id"]
        for m in monsters
    }
    selected_monster = st.selectbox("전투할 몬스터", list(monster_options.keys()))
    selected_monster_id = monster_options[selected_monster]
    selected_monster_data = next((m for m in monsters if m.get("actor_id") == selected_monster_id), None)
    if selected_monster_data:
        reward_preview = selected_monster_data.get("expected_reward") or {}
        with st.container(border=True):
            st.markdown(f"### 👹 {selected_monster_data.get('name')} Lv.{selected_monster_data.get('level', 1)}")
            st.caption("처치 시 예상 보상")
            st.write(f"EXP: **+{reward_preview.get('exp', 0)}**")
            items = reward_preview.get("items") or []
            if items:
                for item in items:
                    prob = item.get("drop_probability", 1.0)
                    prob_text = f" ({int(prob * 100)}%)" if prob is not None else ""
                    st.write(f"- {item.get('name')} × {item.get('quantity', 1)}{prob_text}")
            else:
                st.write("- 아이템 보상 없음")

    if st.button("전투 시작"):
        start_res = request("POST", "/battle/start", json={"monster_id": selected_monster_id})
        if start_res is not None and start_res.status_code == 200:
            battle = start_res.json()
            st.session_state.battle_id = battle.get("battle_id")
            st.session_state.last_battle_log = ["전투를 시작했습니다."]
            st.success("전투 시작!")
            st.rerun()
        elif start_res is not None:
            st.error(start_res.json().get("detail", "전투 시작 실패"))

    if equipped:
        eq_df = pd.DataFrame(equipped)[["slot_no", "id", "name", "mp_cost", "cooldown_sec"]]
        eq_df.columns = ["슬롯", "스킬 ID", "스킬명", "MP", "쿨다운"]
        st.markdown("### 장착 스킬")
        st.dataframe(eq_df, use_container_width=True, hide_index=True)
    else:
        st.warning("장착된 스킬이 없습니다. Skills 페이지에서 스킬을 먼저 장착해주세요.")

with right:
    st.subheader("전투 상태")
    if not st.session_state.battle_id:
        st.info("전투를 시작하면 상태가 표시됩니다.")
    else:
        status_res = request("GET", "/battle/status", params={"battle_id": st.session_state.battle_id})
        if status_res is not None and status_res.status_code == 200:
            status = status_res.json()
            monster = status.get("monster", {})
            battle_status = status.get("status")
            max_hp = monster.get("max_hp", 0) or 1
            cur_hp = monster.get("current_hp", 0)

            player = status.get("character", {})
            st.metric("전투 상태", battle_status)

            p_hp = int(player.get("hp", 0))
            p_max_hp = max(1, int(player.get("max_hp", 1)))
            p_mp = int(player.get("mp", 0))
            p_max_mp = max(1, int(player.get("max_mp", 1)))

            st.markdown("### 플레이어")
            st.write(f"**{player.get('character_name')}** Lv.{player.get('level')}")
            exp = int(player.get("exp", 0) or 0)
            exp_to_next = player.get("exp_to_next")
            if exp_to_next:
                exp_to_next = max(1, int(exp_to_next))
                st.write(f"EXP: {exp} / {exp_to_next}")
                st.progress(max(0.0, min(1.0, exp / exp_to_next)))
            else:
                st.write(f"EXP: {exp}")
            st.write(f"HP: {p_hp} / {p_max_hp}")
            st.progress(max(0.0, min(1.0, p_hp / p_max_hp)))
            st.write(f"MP: {p_mp} / {p_max_mp}")
            st.progress(max(0.0, min(1.0, p_mp / p_max_mp)))

            st.markdown("### 몬스터")
            st.write(f"**👹 {monster.get('name')}** Lv.{monster.get('level', 1)}")
            st.progress(max(0.0, min(1.0, cur_hp / max_hp)))
            st.write(f"HP: {cur_hp} / {max_hp}")
            st.write(f"ATK: {monster.get('atk')} / DEF: {monster.get('def')}")
            expected_reward = monster.get("expected_reward") or {}
            with st.container(border=True):
                st.caption("🎁 처치 시 예상 보상")
                st.write(f"EXP: **+{expected_reward.get('exp', 0)}**")
                reward_items = expected_reward.get("items") or []
                if reward_items:
                    for item in reward_items:
                        prob = item.get("drop_probability", 1.0)
                        prob_text = f" ({int(prob * 100)}%)" if prob is not None else ""
                        st.write(f"- {item.get('name')} × {item.get('quantity', 1)}{prob_text}")
                else:
                    st.write("- 아이템 보상 없음")

            if battle_status == "ACTIVE":
                st.markdown("### 공격")
                if not equipped:
                    st.info("사용 가능한 장착 스킬이 없습니다.")
                else:
                    for skill in equipped:
                        label = f"Slot {skill.get('slot_no')} - {skill.get('name')}"
                        if st.button(label, key=f"attack_{skill.get('id')}"):
                            atk_res = request(
                                "POST",
                                "/battle/attack",
                                json={"battle_id": st.session_state.battle_id, "skill_id": skill.get("id")},
                            )
                            if atk_res is not None and atk_res.status_code == 200:
                                result = atk_res.json()
                                st.session_state.last_battle_log.append(result.get("message", "공격했습니다."))
                                battle_result = result.get("battle", {})
                                if battle_result.get("status") == "FAILED":
                                    st.session_state.last_battle_log.append("전투 실패: HP가 0이 되었습니다. Inventory에서 회복 아이템을 사용할 수 있습니다.")
                                reward = result.get("reward")
                                if reward:
                                    level_info = reward.get("level") or {}
                                    level_text = ""
                                    if level_info.get("leveled_up"):
                                        level_text = f" / 레벨업: Lv.{level_info.get('level_before')} → Lv.{level_info.get('level_after')} (HP/MP 회복)"
                                    st.session_state.last_battle_log.append(
                                        f"보상 획득: EXP {reward.get('exp', 0)}, Items {reward.get('items', [])}{level_text}"
                                    )
                                st.rerun()
                            elif atk_res is not None:
                                st.error(atk_res.json().get("detail", "공격 실패"))
            else:
                if battle_status == "FAILED":
                    st.error("전투 실패! 회복 아이템을 사용한 뒤 다시 도전할 수 있습니다.")
                elif battle_status == "COMPLETED":
                    st.success("전투 승리! 보상이 지급되었다면 Inventory에서 확인할 수 있습니다.")
                else:
                    st.info("전투가 종료되었습니다.")
                if st.button("전투 상태 초기화"):
                    st.session_state.battle_id = None
                    st.rerun()
        elif status_res is not None:
            st.error(status_res.json().get("detail", "전투 상태 조회 실패"))
            st.session_state.battle_id = None

st.divider()
st.subheader("전투 로그")
for log in reversed(st.session_state.last_battle_log[-10:]):
    st.write(f"- {log}")
