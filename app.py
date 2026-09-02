import streamlit as st
from dotenv import load_dotenv
from game_state import init_game_state
from game_logic import get_llm
from story_llm import generate_protagonist
from npc_generator import generate_npcs
from ui_sidebar import render_npc_sidebar
from ui_game import render_intro, render_playing, render_result, render_ending
from ui_theme import inject_theme
from parsing_json import JSONInvokeError

load_dotenv()

APP_TITLE = "👑 여왕이 되고 싶어"

st.set_page_config(page_title="여왕이 되고 싶어", page_icon="👑", layout="centered")
inject_theme()


def init_session():
    defaults = {
        "phase": "intro",
        "player_name": "",
        "protagonist": None,
        "current_event": None,
        "npcs": None,
        "game_state": None,
        "current_event_idx": 0,
        "is_hidden": False,
        "hint": None,
        "pending_result": None,
        "ending_type": None,
        "epilogue": None,
        "npc_chat_target": None,
        "npc_chat_history": {},
        "event_npc_line": None,
        "next_event_ready": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def start_game():
    llm = get_llm(0.9)
    with st.spinner("주인공 정보를 생성하는 중..."):
        protagonist = generate_protagonist(llm)
        if st.session_state.player_name.strip():
            original_name = protagonist["이름"]
            new_name = st.session_state.player_name.strip()
            protagonist["이름"] = new_name
            for field in ["출신", "입궁계기"]:
                if field in protagonist and original_name in protagonist[field]:
                    protagonist[field] = protagonist[field].replace(original_name, new_name)

    with st.spinner("궁중 인물들을 소환하는 중..."):
        npcs = generate_npcs(llm, protagonist)

    game_state = init_game_state(protagonist, npcs)

    with st.spinner("이야기를 준비하는 중..."):
        from story_llm import generate_story_event
        first_event = generate_story_event(
            llm, protagonist, npcs, game_state,
            stage_no=1, hidden_mode=False
        )

    st.session_state.update({
        "protagonist": protagonist,
        "npcs": npcs,
        "game_state": game_state,
        "current_event": first_event,
        "current_event_idx": 1,
        "is_hidden": False,
        "hint": None,
        "pending_result": None,
        "ending_type": None,
        "epilogue": None,
        "npc_chat_target": None,
        "npc_chat_history": {},
        "event_npc_line": None,
        "phase": "playing",
    })


init_session()
phase = st.session_state.phase

if st.session_state.npcs and phase in {"playing", "result", "ending"}:
    render_npc_sidebar()

if phase != "intro":
    st.title(APP_TITLE)


def route(phase: str):
    if phase == "loading":
        start_game()
        st.rerun()
    elif phase == "playing":
        render_playing()
    elif phase == "result":
        render_result()
    elif phase == "ending":
        render_ending()
    else:
        render_intro()


try:
    route(phase)
except JSONInvokeError:
    st.error("궁중의 소식이 끊겼습니다. 잠시 후 다시 청해 주십시오.")
    if st.button("다시 시도", use_container_width=True, type="primary"):
        st.rerun()
