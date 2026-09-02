import time

import streamlit as st
from game_logic import get_llm, get_current_event, get_gpt_hint, handle_choice, force_to_end_game, generate_next_event
from game_state import (
    ROUTE_THRONE,
    ENDING_DEATH,
    ENDING_QUEEN,
    ENDING_PURGED,
    ENDING_THRONE,
    ENDING_FOUND,
)
from ui_sidebar import render_npc_chat
from ui_theme import render_stat_plate, render_rank_ladder

APP_TITLE = "👑 간택은 제가 하겠습니다, 전하"


def render_intro():
    st.title(APP_TITLE)
    st.divider()
    st.info("깊은 구중궁궐로 들어가면 다시는 나오기 어렵습니다.\n\n"
            "후궁은 중전이 될 수 없습니다. 국법이 그러합니다.\n\n"
            "숙원으로 입궁하여, 그 국법을 넘어서십시오. "
            "중전의 자리에, 나아가 그 위의 자리까지.")
    st.caption("중전은 거쳐 갈 뿐입니다 — 만약 조선에 여왕이 있었다면.")
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input("이름을 입력하세요", value=st.session_state.player_name)
        st.session_state.player_name = name_input
        st.write("")
        if st.button("입궁하겠습니까?", use_container_width=True, type="primary"):
            st.session_state.phase = "loading"
            st.rerun()


TYPE_SPEED = 0.009   # 글자당 초. 4~6문장이면 2초 안팎


def render_typed(text: str, key: str):
    """사건 본문을 한 글자씩 흘린다. 같은 사건은 한 번만 친다."""
    typed = st.session_state.setdefault("typed_events", set())

    if key in typed:
        st.write(text)
        return

    placeholder = st.empty()
    shown = ""
    for ch in text:
        shown += ch
        placeholder.markdown(shown)
        time.sleep(TYPE_SPEED)
    typed.add(key)


def render_playing():
    if st.session_state.npc_chat_target:
        render_npc_chat()
        return

    p = st.session_state.protagonist
    event = get_current_event()
    game_state = st.session_state.game_state

    if event is None:
        force_to_end_game()
        st.rerun()
        return

    render_stat_plate(
        p["이름"],
        game_state["현재품계"],
        game_state["총애"],
        game_state["권세"],
        game_state["위험도"],
    )
    render_rank_ladder(game_state["현재품계"])

    st.divider()

    if st.session_state.is_hidden:
        route = game_state.get("루트")
        route_label = "반정 — 스스로 옥좌에 오른다" if route == ROUTE_THRONE else "역성혁명 — 새 왕조를 연다"
        st.warning(f"히든 · {route_label}  |  {event.get('제목', '')}")
    else:
        st.subheader(f"{event.get('제목', '')}")

    render_typed(event["상황"], key=f"{st.session_state.is_hidden}-{st.session_state.current_event_idx}")
    st.divider()

    # 사건에 끼어드는 인물. 이벤트를 만들 때 같이 생성되므로 추가 호출이 없다.
    if event.get("등장대사"):
        with st.chat_message("assistant", avatar="💬"):
            st.caption(event.get("등장인물", ""))
            st.write(event["등장대사"])

        st.divider()

    # 상궁의 조언
    if st.session_state.hint:
        with st.chat_message("assistant", avatar="👩‍🦳"):
            st.caption("상궁의 조언")
            st.write(st.session_state.hint)
    else:
        if st.button("🕯️ 상궁의 조언 구하기"):
            llm = get_llm(0.3)
            with st.spinner("상궁이 생각에 잠겼습니다..."):
                hint = get_gpt_hint(event["상황"], llm)
            st.session_state.hint = hint
            st.rerun()

    st.write("")
    st.write("**어떻게 하시겠습니까?**")

    for choice in event.get("표시선택지", []):
        is_gamble = choice.get("선택성향") == "위험한 승부수"
        prefix = "🎲 " if is_gamble else ""
        label = f"{prefix}{choice['번호']}. {choice['행동']}"
        if st.button(label, key=f"c_{choice['번호']}", use_container_width=True, type="secondary"):
            handle_choice(event, choice["번호"])
            st.rerun()


def render_result():
    p = st.session_state.pending_result
    if not p:
        st.session_state.phase = "playing"
        st.rerun()
        return

    st.write(p["서사"])
    st.divider()

    game_state = st.session_state.game_state

    if p.get("승급"):
        info = p["승급"]
        st.success(f"✨ {info['이전품계']} → **{info['현재품계']}** 으로 승급하였습니다!")

    if p.get("강등"):
        info = p["강등"]
        st.error(f"⚠️ {info['이전품계']} → **{info['현재품계']}** 으로 강등되었습니다.")

    if p.get("루트확정"):
        route = p["루트확정"]
        st.subheader("👑 중전 책봉")
        if route == ROUTE_THRONE:
            st.info("**외조가 당신의 편에 섰습니다.**\n\n"
                    "영의정이 은밀히 뜻을 같이하겠다 전해왔습니다. "
                    "명분을 쌓아 반정을 일으키고, 스스로 옥좌에 오르는 길이 열렸습니다.")
        else:
            st.error("**사대부는 끝내 당신을 인정하지 않았습니다.**\n\n"
                     "조정의 문은 닫혔습니다. 그렇다면 남은 길은 하나뿐입니다. "
                     "조정을 통째로 갈아엎고 새 왕조를 여는 것.")

    st.subheader("📊 현재 상태")
    prev = p.get("이전스탯", {})
    col1, col2, col3 = st.columns(3)

    def delta_str(key):
        diff = game_state[key] - prev.get(key, game_state[key])
        if diff > 0: return f"+{diff}"
        if diff < 0: return str(diff)
        return None

    col1.metric("총애", game_state["총애"], delta=delta_str("총애"))
    col2.metric("권세", game_state["권세"], delta=delta_str("권세"))
    col3.metric("위험도", game_state["위험도"], delta=delta_str("위험도"), delta_color="inverse")

    if st.session_state.is_hidden:
        st.caption("⚠️ 중전에게는 강등이 없습니다. 폐위가 있을 뿐이고, 그것은 곧 죽음입니다.")

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn = "히든 스토리 시작..." if p.get("루트확정") else "▶ 계속하기"
        if st.button(btn, use_container_width=True, type="primary"):
            st.session_state.pending_result = None
            with st.spinner("다음 이야기를 준비하는 중..."):
                generate_next_event()
            st.session_state.phase = "playing"
            st.rerun()


ENDING_VIEW = {
    ENDING_DEATH: ("error", "💀", "{name}의 이야기가 여기서 끝났습니다.", False),
    ENDING_PURGED: ("error", "⚰️", "폐비 {name} — 사약이 내려졌습니다.", False),
    ENDING_QUEEN: ("success", "👑", "중전 {name}", True),
    ENDING_THRONE: ("success", "⚡", "여왕 {name} — 조선 최초의 여왕", True),
    ENDING_FOUND: ("success", "🔥", "태조 {name} — 새 왕조를 열다", True),
}


def render_ending():
    p = st.session_state.protagonist
    ending_type = st.session_state.ending_type
    pending = st.session_state.pending_result

    if pending:
        st.write(pending["서사"])
        st.divider()

    view = ENDING_VIEW.get(ending_type)
    if view:
        kind, icon, template, celebrate = view
        text = f"{icon} " + template.format(name=p["이름"])
        (st.success if kind == "success" else st.error)(text)
        if celebrate:
            st.balloons()

    st.write(st.session_state.epilogue)
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("다시 입궁하겠습니까?", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
