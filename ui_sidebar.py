import streamlit as st
from npc_generator import generate_npc_dialogue
from game_logic import get_llm
from game_state import AUDIENCE_PER_STAGE, apply_relation_change
from ui_theme import render_audience_candles

# 관계 키 -> (아이콘, 기본 호칭, 대화 버튼 문구)
NPC_VIEW = {
    "왕":      ("👑", "전하", "{}께 문안 올리기"),
    "대비":    ("🔥", "대비", "{}께 문안 올리기"),
    "중전":    ("👸", "중전", "{}께 문안 올리기"),
    "경쟁후궁": ("🗡️", "경쟁후궁", "{}와 이야기하기"),
    "우호후궁": ("🤍", "우호후궁", "{}와 이야기하기"),
    "상궁":    ("👩‍🦳", "상궁", "{}에게 조언 구하기"),
    "영의정":   ("📜", "영의정", "{}과 은밀히 만나기"),
}

# 사이드바에 세울 순서
NPC_ORDER = ["왕", "대비", "중전", "경쟁후궁", "우호후궁", "상궁", "영의정"]


def audience_left() -> int:
    return st.session_state.game_state.get("문안횟수", AUDIENCE_PER_STAGE)


def display_name(rel_key: str) -> str:
    icon, default, _ = NPC_VIEW.get(rel_key, ("💬", rel_key, "{}와 대화하기"))
    return st.session_state.npcs.get(rel_key, {}).get("이름", default)


def render_npc_row(rel_key, disabled=False):
    npc = st.session_state.npcs.get(rel_key)
    if npc is None:
        return

    icon, _, label_fmt = NPC_VIEW[rel_key]
    rel = st.session_state.game_state["관계"].get(rel_key, 30)
    name = display_name(rel_key)

    st.subheader(f"{icon} {name}")
    st.caption(f"{rel}/100")
    st.progress(rel / 100)
    if st.button(label_fmt.format(name), key=f"talk_{rel_key}",
                 use_container_width=True, disabled=disabled):
        st.session_state.npc_chat_target = rel_key
        st.rerun()
    st.divider()


def render_npc_sidebar():
    left = audience_left()
    # 대화창은 이벤트 화면에서만 열린다. 결과/엔딩 화면에서 누르면
    # 창이 뜨지 않은 채 상태만 바뀌어 다음 이벤트를 가려버린다.
    in_event = st.session_state.phase == "playing"
    no_audience = left <= 0 or not in_event

    with st.sidebar:
        st.title("👑 간택은 제가 하겠습니다")
        st.divider()

        st.title("👥 궁중 인물")
        render_audience_candles(left, AUDIENCE_PER_STAGE)
        if not in_event:
            st.info("문안은 이야기를 진행하는 중에만 드릴 수 있습니다.")
        elif no_audience:
            st.warning("오늘의 문안이 모두 끝났습니다. 이야기를 진행하십시오.")
        st.divider()

        for rel_key in NPC_ORDER:
            render_npc_row(rel_key, disabled=no_audience)


def queue_ripple_toast(changes: dict, target: str, risk_delta: int):
    """st.rerun() 뒤에 보여줄 토스트를 쌓아둔다."""
    queue = st.session_state.setdefault("pending_toasts", [])

    main = changes.get(target, 0)
    if main > 0:
        queue.append((f"{display_name(target)} 관계도 +{main} 🤝", "✅"))
    elif main < 0:
        queue.append((f"{display_name(target)} 관계도 {main} 😠", "⚠️"))

    side = [f"{display_name(k)} {v:+d}" for k, v in changes.items() if k != target]
    if side:
        queue.append(("소문이 궁 안에 퍼집니다 — " + ", ".join(side), "🌫️"))

    if risk_delta:
        queue.append((f"총애를 받을수록 표적이 됩니다. 위험도 +{risk_delta}", "🔥"))


def flush_toasts():
    for text, icon in st.session_state.pop("pending_toasts", []):
        st.toast(text, icon=icon)


def render_npc_chat():
    flush_toasts()
    rel_key = st.session_state.npc_chat_target
    npc = st.session_state.npcs.get(rel_key, {})
    game_state = st.session_state.game_state
    rel = game_state["관계"].get(rel_key, 30)
    left = audience_left()

    icon, _, _ = NPC_VIEW.get(rel_key, ("💬", rel_key, ""))
    name = display_name(rel_key)

    st.subheader(f"{icon} {name}와의 대화")
    st.caption(f"{rel}/100")
    st.progress(rel / 100)
    render_audience_candles(left, AUDIENCE_PER_STAGE)
    st.divider()

    if rel_key not in st.session_state.npc_chat_history:
        st.session_state.npc_chat_history[rel_key] = [
            {"role": "npc", "text": npc.get("첫인상대사", "..."), "표정": "바라보며"}
        ]

    history = st.session_state.npc_chat_history[rel_key]

    for msg in history:
        if msg["role"] == "player":
            with st.chat_message("user", avatar="🙋🏻‍♀️"):
                st.write(msg["text"])
        else:
            with st.chat_message("assistant", avatar=icon):
                st.caption(msg.get("표정", ""))
                st.write(msg["text"])

    st.divider()

    if left <= 0:
        st.info("오늘의 문안이 모두 끝났습니다. 이야기로 돌아가십시오.")
    else:
        player_input = st.chat_input("무슨 말을 하시겠습니까?")
        if player_input:
            llm = get_llm(0.8)
            with st.spinner("..."):
                result = generate_npc_dialogue(
                    llm, rel_key, npc, rel, player_input, history=history
                )

            history.append({"role": "player", "text": player_input})
            history.append({"role": "npc", "text": result["대사"], "표정": result.get("속내", "")})
            st.session_state.npc_chat_history[rel_key] = history

            game_state["문안횟수"] = max(0, left - 1)

            change = int(result.get("관계변화제안", 0) or 0)
            changes, risk_delta = apply_relation_change(game_state, rel_key, change)
            queue_ripple_toast(changes, rel_key, risk_delta)
            st.rerun()

    if st.button("**← 이벤트로 돌아가기**", use_container_width=True):
        st.session_state.npc_chat_target = None
        st.rerun()
