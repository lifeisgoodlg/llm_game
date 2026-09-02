import streamlit as st
from langchain_openai import ChatOpenAI
from game_state import (
    resolve_player_choice,
    decide_route,
    AUDIENCE_PER_STAGE,
    ENDING_DEATH,
    ENDING_QUEEN,
    ENDING_PURGED,
    ENDING_THRONE,
    ENDING_FOUND,
)
from story_llm import generate_epilogue

APP_MODEL = "gpt-4o-mini"

MAIN_STAGES = 10
HIDDEN_STAGES = 3

FINAL_ENDINGS = [ENDING_DEATH, ENDING_QUEEN, ENDING_PURGED, ENDING_THRONE, ENDING_FOUND]


def get_llm(temp: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(model=APP_MODEL, temperature=temp)


def get_current_event():
    return st.session_state.get("current_event")


def generate_next_event():
    from story_llm import generate_story_event
    llm = get_llm(0.9)
    protagonist = st.session_state.protagonist
    npcs = st.session_state.npcs
    game_state = st.session_state.game_state
    is_hidden = st.session_state.is_hidden

    stage_no = st.session_state.current_event_idx + 1
    max_stage = HIDDEN_STAGES if is_hidden else MAIN_STAGES

    if stage_no > max_stage:
        st.session_state.current_event = None
        return

    st.session_state.current_event = generate_story_event(
        llm, protagonist, npcs, game_state,
        stage_no=stage_no, hidden_mode=is_hidden
    )


def get_gpt_hint(situation: str, llm: ChatOpenAI) -> str:
    prompt = f"""
조선 궁중 생활 삼십 년의 노련한 상궁으로서 아래 상황에 짧은 조언을 해주세요.
2문장 이내로, 어떤 선택이 현명할지 암시만 하세요. 정답을 직접 말하지 마세요.
고풍스럽고 은유적인 말투로 답하세요.

상황: {situation}

조언:
"""
    return llm.invoke(prompt).content.strip()


def finish_game(ending_type: str, narrative=None):
    """엔딩을 확정하고 에필로그를 생성한다."""
    protagonist = st.session_state.protagonist
    game_state = st.session_state.game_state

    epilogue = generate_epilogue(
        get_llm(0.3), protagonist, ending_type, game_state.get("현재품계", "숙원")
    )
    st.session_state.update(
        ending_type=ending_type,
        epilogue=epilogue,
        pending_result={"서사": narrative} if narrative else None,
        phase="ending",
    )


def handle_choice(event: dict, selected_label: str):
    protagonist = st.session_state.protagonist
    game_state = st.session_state.game_state
    is_hidden = st.session_state.is_hidden

    prev_stats = {
        "총애": game_state["총애"],
        "권세": game_state["권세"],
        "위험도": game_state["위험도"],
    }

    result = resolve_player_choice(event, selected_label, game_state, is_hidden)
    outcome = result["판정결과"]
    narrative = result["서사결과"]

    ending = game_state.get("엔딩")

    if ending in FINAL_ENDINGS:
        # 사망 / 폐위사사 / 여왕등극 / 개국 은 그 자리에서 끝난다
        finish_game(ending, narrative)
    else:
        st.session_state.pending_result = {
            "서사": narrative,
            "승급": outcome.get("승급"),
            "강등": outcome.get("강등"),
            "이전스탯": prev_stats,
            "루트확정": None,
        }

        if game_state["현재품계"] == "중전" and not is_hidden:
            # 중전에 오르는 순간 히든이 열리고, 외조의 지지 여부로 길이 갈린다
            st.session_state.is_hidden = True
            st.session_state.current_event_idx = 0
            st.session_state.pending_result["루트확정"] = decide_route(game_state)
        else:
            st.session_state.current_event_idx += 1

        # 날이 바뀌면 문안 횟수가 회복된다
        game_state["문안횟수"] = AUDIENCE_PER_STAGE
        st.session_state.phase = "result"

    st.session_state.hint = None
    st.session_state.event_npc_line = None
    st.session_state.game_state = game_state


def force_to_end_game():
    """마지막 단계까지 왔는데 아무 엔딩도 확정되지 않은 경우."""
    game_state = st.session_state.game_state
    current_rank = game_state.get("현재품계", "")

    ending_type = game_state.get("엔딩")
    if ending_type not in FINAL_ENDINGS:
        if st.session_state.is_hidden or current_rank == "중전":
            # 히든에 진입했다는 것은 이미 중전에 올랐다는 뜻이다
            ending_type = ENDING_QUEEN
        else:
            # 마지막 단계까지 중전에 오르지 못하면 궁에서 살아남지 못한다
            ending_type = ENDING_DEATH
            game_state["생존"] = False
        game_state["엔딩"] = ending_type

    finish_game(ending_type)
