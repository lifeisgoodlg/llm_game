from game_state import (
    normalize_choices,
    ROUTE_THRONE,
    ROUTE_FOUND,
    ENDING_DEATH,
    ENDING_QUEEN,
    ENDING_PURGED,
    ENDING_THRONE,
    ENDING_FOUND,
)
from parsing_json import invoke_json
from langchain_openai import ChatOpenAI

WRITER_SYSTEM = "조선 궁중 암투 드라마 작가입니다. JSON만 출력합니다."

# 품계별 메인 스토리 테마
RANK_THEMES = {
    "숙원": "입궁 초기 — 궁중 법도 익히기, 첫 문안, 나인들의 텃세와 서열 파악",
    "소원": "승은(承恩) — 왕의 눈에 들기, 첫 대면, 후궁들의 견제",
    "숙용": "궁의 냉혹함 — 가까운 이의 죽음, 상실, 침묵해야 할 때를 배우는 순간",
    "소용": "모함 — 저주 인형, 증거 조작, 누명, 내명부의 국문",
    "숙의": "회임 — 원자를 향한 위협, 의녀 매수, 산실청을 둘러싼 암투",
    "소의": "외조(外朝) — 붕당과의 연결, 언관의 상소와 탄핵, 친정 세력 다지기",
    "귀인": "곤위(坤位)를 흔들다 — 중전의 결정적 약점, 대비와의 첫 정면 충돌",
    "빈": "폐비와 책봉 — 중전 폐위, 후궁은 중전이 될 수 없다는 국법과의 싸움",
    "중전": "중전의 시련 — 사림의 반발, 세자 책봉, 대비의 견제",
}

# 히든 스토리 — 루트별 3단계
HIDDEN_THEMES = {
    ROUTE_THRONE: {
        1: "명분 — 왕의 실정을 기록으로 남기고 종친과 대간을 포섭한다. 반정에는 명분이 필요하다.",
        2: "병권 — 훈련도감과 어영청의 대장을 포섭한다. 반정은 결국 군사 정변이다.",
        3: "즉위 — 옥새를 쥐고 종묘에 고한다. 신하들은 종친 남자를 앉히려 한다. 그것을 뚫어야 한다.",
    },
    ROUTE_FOUND: {
        1: "천명(天命) — 조선의 명운이 다했다는 논리를 만든다. 도참과 재이, 그리고 민심.",
        2: "조정 장악 — 반대하는 대신을 제거하고 인사권과 군권을 손에 쥔다.",
        3: "개국 — 국호를 정하고 종묘를 갈아엎는다. 오백 년 사직을 끝내고 새 왕조를 연다.",
    },
}


# 주인공 생성
def generate_protagonist(llm: ChatOpenAI) -> dict:
    prompt = """
조선 왕조 궁중 암투극의 주인공을 생성하세요.
주인공은 온순해 보이지만 속으로는 냉철한 야심가입니다.
반드시 JSON만 출력하세요.
{
  "이름": "조선식 여성 이름 (예: 윤소원, 최인영)",
  "출신": "몰락한 사대부가 또는 중인/천민 출신 배경 (2문장, 입궁 전 고난 포함)",
  "초기품계": "숙원 또는 소원 중 하나",
  "성격": "겉으론 유순하나 속으론 냉혹한 성격 묘사 (한 문장)",
  "특기": "의술/독약/서예/침선/산술 중 하나",
  "입궁계기": "절박한 사연으로 입궁하게 된 배경 (2~3문장, 복수나 생존이 동기)"
}
"""
    return invoke_json(
        llm,
        WRITER_SYSTEM,
        prompt,
        validate=lambda d: "이름" in d and "초기품계" in d,
    )


def get_relationship_snapshot(state: dict, npcs: dict) -> str:
    def name_of(key, default):
        return npcs.get(key, {}).get("이름", default)

    rel = state["관계"]
    return (
        f"전하 {rel['왕']}/100 | {name_of('대비', '대비')} {rel['대비']}/100 | "
        f"{name_of('중전', '중전')} {rel['중전']}/100\n"
        f"{name_of('경쟁후궁', '경쟁후궁')} {rel['경쟁후궁']}/100 | "
        f"{name_of('우호후궁', '우호후궁')} {rel['우호후궁']}/100 | "
        f"{name_of('상궁', '상궁')} {rel['상궁']}/100 | "
        f"{name_of('영의정', '영의정')} {rel['영의정']}/100\n"
        f"총애 {state['총애']} | 권세 {state['권세']} | 위험도 {state['위험도']} | 품계 {state['현재품계']}"
    )


def valid_event(data: dict) -> bool:
    """선택지 3개와 판정에 꼭 필요한 필드가 다 왔는지 확인한다."""
    choices = data.get("선택지", [])
    if len(choices) != 3:
        return False
    required = ("행동", "성공시서술", "실패시서술", "효과")
    return all(all(key in choice for key in required) for choice in choices)


# 스토리 이벤트 생성
def generate_story_event(
    llm: ChatOpenAI,
    protagonist: dict,
    npcs: dict,
    state: dict,
    stage_no: int,
    hidden_mode: bool = False,
    retriever=None,
) -> dict:
    route = state.get("루트") or ROUTE_THRONE

    if hidden_mode:
        stage_theme = HIDDEN_THEMES[route].get(stage_no, "궁중 암투")
        mode_line = (
            "중전에 오른 뒤 스스로 왕위에 오르려 한다 (반정)"
            if route == ROUTE_THRONE
            else "중전에 오른 뒤 조선을 끝내고 새 왕조를 열려 한다 (역성혁명)"
        )
    else:
        stage_theme = RANK_THEMES.get(state["현재품계"], "궁중 암투")
        mode_line = "입궁 ~ 중전 등극 이전"

    rag_context = ""
    if retriever is not None:
        from rag_pipeline import retrieve_context
        query = f"{stage_theme} {state['현재품계']} {protagonist['특기']}"
        rag_context = f"참고 고증:\n{retrieve_context(query, retriever)}\n\n"

    system = """
조선 궁중 암투 게임 시나리오 작가입니다.
반드시 JSON만 출력하세요.
규칙: 선택지 3개 필수 / 정답 구조 금지 / 승급, 사망 확정 금지 / 스탯, 관계 변화만 제안
"""

    prompt = f"""
{rag_context}[주인공]
이름: {protagonist['이름']} | 품계: {state['현재품계']} | 특기: {protagonist['특기']}
성격: {protagonist['성격']}
입궁계기: {protagonist['입궁계기']}

[관계 및 스탯]
{get_relationship_snapshot(state, npcs)}

[인물]
전하: {npcs.get('왕', {}).get('성격', '')}
{npcs.get('대비', {}).get('이름', '대비')}: {npcs.get('대비', {}).get('성격', '')} / 장악한붕당: {npcs.get('대비', {}).get('장악한붕당', '')}
{npcs.get('중전', {}).get('이름', '중전')}: {npcs.get('중전', {}).get('성격', '')} / 친정: {npcs.get('중전', {}).get('친정', '')}
{npcs.get('경쟁후궁', {}).get('이름', '경쟁후궁')}: {npcs.get('경쟁후궁', {}).get('성격', '')}
{npcs.get('우호후궁', {}).get('이름', '우호후궁')}: {npcs.get('우호후궁', {}).get('성격', '')} / 도움방식: {npcs.get('우호후궁', {}).get('도움방식', '')} / 배신가능성: {npcs.get('우호후궁', {}).get('배신가능성', '')}
{npcs.get('상궁', {}).get('이름', '상궁')}: {npcs.get('상궁', {}).get('성격', '')}
{npcs.get('영의정', {}).get('이름', '영의정')}: {npcs.get('영의정', {}).get('성격', '')} / 정치성향: {npcs.get('영의정', {}).get('정치성향', '')} / 포섭조건: {npcs.get('영의정', {}).get('포섭조건', '')}

[이번 단계]
단계: {stage_no} | 테마: {stage_theme}
모드: {mode_line}

[배경 규칙 - 반드시 지킬 것]
- 조선 왕조. 명나라/청나라가 아니라 조선의 제도와 호칭을 쓴다 (전하, 마마, 중전, 대비, 내명부, 승정원, 사헌부, 사간원).
- 후궁은 원칙적으로 중전(왕비)이 될 수 없다. 중전 자리가 비어야 하고, 전하가 밀어붙여야 하고, 사림의 반대를 뚫어야 한다.
- 언관(사헌부·사간원)은 왕의 사생활까지 탄핵한다. 총애를 받을수록 상소가 올라온다.
- 대비는 왕보다 위계가 높다. 내명부의 최종 권력자다.

[효과 수치 가이드 - 반드시 이 범위 안에서 채울 것]
strategic: 총애 -5~+20,  권세 -5~+18,  위험도 -10~+15
safe:      총애 -3~+12,  권세 -3~+10,  위험도 -15~+5
gamble:    총애 -15~+35, 권세 -10~+30, 위험도 -5~+35
관계변화: 각 -15~+15 범위

[출력 형식]
{{
  "단계": {stage_no},
  "현재품계": "{state['현재품계']}",
  "제목": "사건 제목",
  "상황": "4~6문장. 누가 돕고 방해하는지 드러나야 함.",
  "선택지": [
    {{
      "choice_id": "strategic",
      "선택성향": "정치적 계산",
      "행동": "행동 한 문장",
      "성공시서술": "2~3문장",
      "실패시서술": "2~3문장",
      "효과": {{"총애": 0, "권세": 0, "위험도": 0, "관계변화": {{"왕": 0, "대비": 0, "중전": 0, "상궁": 0, "경쟁후궁": 0, "우호후궁": 0, "영의정": 0}}}},
      "직접사망가능": false,
      "사망위험임계치": 100
    }},
    {{
      "choice_id": "safe",
      "선택성향": "신중한 보존",
      "행동": "행동 한 문장",
      "성공시서술": "2~3문장",
      "실패시서술": "2~3문장",
      "효과": {{"총애": 0, "권세": 0, "위험도": 0, "관계변화": {{"왕": 0, "대비": 0, "중전": 0, "상궁": 0, "경쟁후궁": 0, "우호후궁": 0, "영의정": 0}}}},
      "직접사망가능": false,
      "사망위험임계치": 100
    }},
    {{
      "choice_id": "gamble",
      "선택성향": "위험한 승부수",
      "행동": "행동 한 문장",
      "성공시서술": "2~3문장",
      "실패시서술": "2~3문장",
      "효과": {{"총애": 0, "권세": 0, "위험도": 0, "관계변화": {{"왕": 0, "대비": 0, "중전": 0, "상궁": 0, "경쟁후궁": 0, "우호후궁": 0, "영의정": 0}}}},
      "직접사망가능": true,
      "사망위험임계치": 100
    }}
  ]
}}

주의: 세 선택지 모두 그럴듯할 것 / safe도 손해 가능 / gamble은 대박, 대참사 모두 가능
우호후궁 관계 높으면 도움 가능, 낮으면 방관
영의정 관계는 훗날 어느 길을 걷게 될지를 가른다. 이 인물을 얻거나 잃는 선택을 종종 섞을 것
"""

    data = invoke_json(llm, system, prompt, validate=valid_event)
    return normalize_choices(data)


# 엔딩 생성
def generate_epilogue(llm: ChatOpenAI, protagonist: dict, ending_type: str, last_rank: str) -> str:
    ending_map = {
        ENDING_DEATH: f"{protagonist['이름']}이 중전에 오르지 못하고 궁중의 암투 속에 스러진",
        ENDING_QUEEN: f"{protagonist['이름']}이 야심을 접고 중전으로서 삶을 마감한",
        ENDING_PURGED: f"{protagonist['이름']}이 중전의 자리에서 역모가 발각되어 폐위되고 사약을 받은",
        ENDING_THRONE: f"{protagonist['이름']}이 반정을 일으켜 조선 최초의 여왕으로 옥좌에 오른",
        ENDING_FOUND: f"{protagonist['이름']}이 조선 오백 년 사직을 끝내고 새 왕조를 연",
    }
    tone_map = {
        ENDING_DEATH: "비극적이고 안타까운 문체. 이름조차 실록에 남지 않았음을 암시할 것",
        ENDING_QUEEN: "쓸쓸하지만 평온한 문체. 오르지 못한 자리를 끝내 바라보는 여운",
        ENDING_PURGED: "가장 무겁고 서늘한 문체. 사약을 받는 장면과 실록의 짧은 한 줄을 대비시킬 것",
        ENDING_THRONE: "웅장하되 위태로운 문체. 옥좌에 앉았으나 신하들의 눈이 여전히 자신을 노린다는 긴장",
        ENDING_FOUND: "웅장하고 고독한 문체. 모든 것을 얻었으나 함께 갈 사람이 남지 않았다는 서늘함",
    }
    prompt = f"""
조선 궁중 암투 드라마의 에필로그를 4~6문장으로 작성하세요.
주인공: {protagonist['이름']} (마지막 품계: {last_rank})
결말: {ending_map.get(ending_type, '')}
문체: {tone_map.get(ending_type, '드라마틱한 문체')}
주인공이 걸어온 험난한 궁중 암투의 삶 전체를 회고하는 방식으로 작성하세요.
"""
    return llm.invoke(prompt).content.strip()
