import random
from copy import deepcopy
from typing import Tuple, Optional

# 조선 내명부 후궁 품계 (종4품 숙원 ~ 정1품 빈) 위에 무품(無品) 중전이 있다.
# 마지막 항목 "빈" 의 승급 조건이 곧 중전 등극 관문이다.
RANKS = ["숙원", "소원", "숙용", "소용", "숙의", "소의", "귀인", "빈", "중전"]

# 히든 루트
ROUTE_THRONE = "즉위"   # 반정으로 스스로 왕위에 오른다
ROUTE_FOUND = "개국"    # 조정을 갈아엎고 새 왕조를 연다

# 엔딩 5종
ENDING_DEATH = "사망"        # 중전에 오르지 못하고 궁에서 스러진다
ENDING_QUEEN = "중전엔딩"     # 중전으로 남는다
ENDING_PURGED = "폐위사사"    # 중전까지 갔으나 역모가 발각된다
ENDING_THRONE = "여왕등극"
ENDING_FOUND = "개국"

# ── 승급 곡선 ────────────────────────────────────────────────
# 표를 손으로 채우지 않고 아래 노브에서 생성한다.
#   (첫 관문 값, 마지막 관문 값, 곡률)
#   곡률 1.0 = 직선 / 1.0 미만 = 초반이 가파름 / 1.0 초과 = 후반이 가파름
RANK_CURVE = {
    "총애":       (20, 100, 0.9),
    "권세":       (12,  88, 1.0),
    "왕호감":      (33,  58, 1.0),
    "위험도_max":  (55, 100, 0.7),
}

# 전체 난이도 배율. 1.0 = 기본, 크면 어려워진다.
DIFFICULTY = 0.65

# 승급 위험도 상한선. 위험도 자체가 0~100 이라 이 위로는 관문이 무의미하다.
RISK_GATE_CEILING = 92

# 한 단계에서 오를 수 있는 최대 품계 수. 숙원에서 중전까지 8번 올라야 하는데
# 메인 스토리가 10단계뿐이라, 스탯이 넘치면 연속 승급을 허용한다.
MAX_PROMOTIONS_PER_STAGE = 2

# ── 히든 최종 관문 ───────────────────────────────────────────
# 두 루트는 서로 다른 스탯을 요구한다. 즉위는 명분(총애와 외조의 지지,
# 낮은 위험도), 개국은 힘(압도적인 권세). 둘은 우열이 아니라 갈림길이다.
#   위험도_min 은 개국에만 있다. 역성혁명은 안전하게 할 수 없다.
THRONE_GATE = {"총애": 85, "권세": 78, "영의정": 60, "위험도_min": 0, "위험도_max": 70}
FOUND_GATE = {"총애": 60, "권세": 88, "영의정": 0, "위험도_min": 60, "위험도_max": 100}

# 히든 진입 시 이 값 이상이면 즉위 루트, 미만이면 개국 루트로 갈린다.
ROUTE_SPLIT_MINISTER = 50


def build_rank_requirements(difficulty: float = DIFFICULTY) -> dict:
    """품계별 승급 조건표를 곡선에서 생성한다."""
    promotable = RANKS[:-1]          # 숙원 ... 빈
    last = len(promotable) - 1
    table = {}

    for i, rank in enumerate(promotable):
        req = {}
        for stat, (start, end, gamma) in RANK_CURVE.items():
            ratio = (i / last) ** gamma if last else 1.0
            value = start + (end - start) * ratio
            if stat == "위험도_max":
                # 위험도 관문은 난이도 배율을 타지 않는다. 배율을 나눠 걸면
                # 100(위험도 상한) 위로 올라가 관문 자체가 사라지기 때문.
                value = min(value, RISK_GATE_CEILING)
            else:
                value = value * difficulty
            req[stat] = int(round(value))
        table[rank] = req

    return table


RANK_UP_REQUIREMENTS = build_rank_requirements()


# 스테이지당 허용되는 문안(사이드바 대화) 횟수
AUDIENCE_PER_STAGE = 3

# 관계 파급 계수: 어떤 인물과 가까워질수록 등을 돌리는 인물들
RELATION_RIPPLE = {
    "왕":      {"대비": -0.5, "중전": -0.6, "경쟁후궁": -0.5},
    "대비":    {"왕": -0.2, "우호후궁": -0.3},
    "중전":    {"왕": -0.2, "우호후궁": -0.4},
    "경쟁후궁": {"우호후궁": -0.3},
    "우호후궁": {"중전": -0.3, "경쟁후궁": -0.3},
    "영의정":   {"대비": -0.4},
    "상궁":    {},
}

# 왕의 총애를 받을수록 표적이 된다
KING_RISK_RATIO = 0.3


def clamp(value, min_v=0, max_v=100):
    return max(min_v, min(max_v, value))


def apply_relation_change(state: dict, target: str, delta: int) -> Tuple[dict, int]:
    """target과의 관계를 delta만큼 바꾸고 다른 인물에게 파급 효과를 준다.

    실제로 변한 인물별 변화량과 위험도 변화량을 돌려준다.
    """
    rels = state["관계"]
    if target not in rels or delta == 0:
        return {}, 0

    before = rels[target]
    rels[target] = clamp(before + delta)
    changes = {target: rels[target] - before}

    for other, ratio in RELATION_RIPPLE.get(target, {}).items():
        if other not in rels:
            continue
        ripple = int(round(delta * ratio))
        if ripple == 0:
            continue
        prev = rels[other]
        rels[other] = clamp(prev + ripple)
        moved = rels[other] - prev
        if moved:
            changes[other] = changes.get(other, 0) + moved

    risk_delta = 0
    if target == "왕" and delta > 0:
        risk_delta = int(round(delta * KING_RISK_RATIO))
        if risk_delta:
            state["위험도"] = clamp(state["위험도"] + risk_delta)

    return changes, risk_delta


def safe_rank_index(rank):
    return RANKS.index(rank) if rank in RANKS else 0


def next_rank(rank):
    idx = safe_rank_index(rank)
    return RANKS[min(idx + 1, len(RANKS) - 1)]


def prev_rank(rank):
    idx = safe_rank_index(rank)
    return RANKS[max(idx - 1, 0)]


# 게임 상태 및 관계 관리
def init_game_state(protagonist: dict, npcs: dict) -> dict:
    rival = npcs.get("경쟁후궁", {})

    return {
        "현재품계": protagonist["초기품계"],
        "총애": 30,
        "권세": 25,
        "위험도": 10,
        "문안횟수": AUDIENCE_PER_STAGE,
        "생존": True,
        "엔딩": None,
        "루트": None,
        "관계": {
            "왕": 42,
            "대비": 15,          # 최종 보스. 가장 적대적으로 시작한다.
            "중전": 20,
            "상궁": 55,
            "경쟁후궁": 30 if rival.get("성향") == "적대적" else 45,
            "우호후궁": 60,
            "영의정": 35,        # 외조. 히든 루트를 가르는 인물.
        },
    }


def decide_route(state: dict) -> str:
    """히든 진입 시 외조의 지지 여부로 길이 갈린다."""
    route = (
        ROUTE_THRONE
        if state["관계"].get("영의정", 0) >= ROUTE_SPLIT_MINISTER
        else ROUTE_FOUND
    )
    state["루트"] = route
    return route


def check_hidden_finale(state: dict) -> Optional[str]:
    """히든 최종 관문을 통과했는지 본다. 통과하면 엔딩을 확정한다."""
    gate = THRONE_GATE if state.get("루트") == ROUTE_THRONE else FOUND_GATE

    if (
        state["총애"] >= gate["총애"]
        and state["권세"] >= gate["권세"]
        and state["관계"].get("영의정", 0) >= gate["영의정"]
        and gate.get("위험도_min", 0) <= state["위험도"] <= gate["위험도_max"]
    ):
        state["엔딩"] = (
            ENDING_THRONE if state["루트"] == ROUTE_THRONE else ENDING_FOUND
        )
        return state["엔딩"]

    return None


def meets_rank_requirement(state: dict, rank: str) -> bool:
    req = RANK_UP_REQUIREMENTS.get(rank)
    if req is None:
        return False
    return (
        state["총애"] >= req["총애"]
        and state["권세"] >= req["권세"]
        and state["관계"]["왕"] >= req["왕호감"]
        and state["위험도"] <= req["위험도_max"]
    )


def promote_if_possible(state: dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """조건이 되는 만큼 승급한다. 한 해에 두 번까지 오를 수 있다."""
    start_rank = state["현재품계"]
    steps = 0

    while steps < MAX_PROMOTIONS_PER_STAGE and meets_rank_requirement(state, state["현재품계"]):
        state["현재품계"] = next_rank(state["현재품계"])
        steps += 1

    if steps:
        return True, start_rank, state["현재품계"]

    return False, None, None


def degrade_if_needed(state: dict, hidden: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
    current_rank = state["현재품계"]

    if state["위험도"] < 95:
        return False, None, None

    # 중전에게는 강등이 없다. 폐위가 있고 그것은 곧 죽음이다.
    if hidden or current_rank == "중전":
        state["생존"] = False
        state["엔딩"] = ENDING_PURGED
        return True, current_rank, None

    if current_rank in ["숙원", "소원"]:
        state["생존"] = False
        state["엔딩"] = ENDING_DEATH
        return True, current_rank, None

    old_rank = current_rank
    state["현재품계"] = prev_rank(current_rank)
    state["위험도"] = max(70, state["위험도"] - 15)
    return True, old_rank, state["현재품계"]


def check_death(state: dict, choice: dict, hidden: bool = False) -> bool:
    fatal_threshold = choice.get("사망위험임계치", 97)
    if choice.get("직접사망가능", False) and state["위험도"] >= fatal_threshold:
        state["생존"] = False
        state["엔딩"] = ENDING_PURGED if hidden else ENDING_DEATH
        return True
    return False


# 선택지 표시/판정
def normalize_choices(event: dict) -> dict:
    event = deepcopy(event)
    raw_choices = event["선택지"]

    for idx, choice in enumerate(raw_choices):
        choice["choice_id"] = choice.get("choice_id", f"choice_{idx+1}")

    shuffled = raw_choices[:]
    random.shuffle(shuffled)

    labels = ["A", "B", "C"]
    display_choices = []
    label_map = {}

    for label, choice in zip(labels, shuffled):
        display_item = {
            "번호": label,
            "choice_id": choice["choice_id"],
            "행동": choice["행동"],
            "선택성향": choice.get("선택성향", "중립"),
        }
        display_choices.append(display_item)
        label_map[label] = choice["choice_id"]

    event["원본선택지"] = raw_choices
    event["표시선택지"] = display_choices
    event["label_map"] = label_map
    return event


def get_choice_by_label(event: dict, selected_label: str) -> dict:
    choice_id = event["label_map"][selected_label]
    for choice in event["원본선택지"]:
        if choice["choice_id"] == choice_id:
            return choice
    raise ValueError(f"선택지 라벨 {selected_label} 에 해당하는 choice를 찾을 수 없습니다.")


def apply_ally_bonus(state: dict, choice: dict) -> dict:
    ally_score = state["관계"].get("우호후궁", 0)
    choice = deepcopy(choice)

    if ally_score >= 75:
        if choice["choice_id"] == "safe":
            choice["효과"]["위험도"] = max(choice["효과"].get("위험도", 0) - 5, -5)
        elif choice["choice_id"] == "strategic":
            choice["효과"]["권세"] = choice["효과"].get("권세", 0) + 3
        elif choice["choice_id"] == "gamble":
            choice["직접사망가능"] = False

    elif ally_score <= 30:
        if choice["choice_id"] == "gamble":
            choice["효과"]["위험도"] = choice["효과"].get("위험도", 0) + 5
        elif choice["choice_id"] == "strategic":
            relation_delta = choice["효과"].setdefault("관계변화", {})
            relation_delta["우호후궁"] = relation_delta.get("우호후궁", 0) - 3

    return choice


def apply_choice_result(state: dict, choice: dict, hidden: bool = False) -> dict:
    effect = choice.get("효과", {})

    state["총애"] = clamp(state["총애"] + effect.get("총애", 0))
    state["권세"] = clamp(state["권세"] + effect.get("권세", 0))
    state["위험도"] = clamp(state["위험도"] + effect.get("위험도", 0))

    for target, delta in effect.get("관계변화", {}).items():
        apply_relation_change(state, target, delta)

    outcome = {
        "사망": False,
        "강등": None,
        "승급": None,
        "히든돌파": None,
    }

    if check_death(state, choice, hidden):
        outcome["사망"] = True
        return outcome

    degraded, old_rank, new_rank = degrade_if_needed(state, hidden)
    if degraded and not state["생존"]:
        outcome["사망"] = True
        return outcome
    if degraded:
        outcome["강등"] = {"이전품계": old_rank, "현재품계": new_rank}

    if hidden:
        # 히든에서는 품계가 아니라 최종 관문을 본다
        outcome["히든돌파"] = check_hidden_finale(state)
        return outcome

    promoted, old_rank, new_rank = promote_if_possible(state)
    if promoted:
        outcome["승급"] = {"이전품계": old_rank, "현재품계": new_rank}

    return outcome


def resolve_player_choice(event: dict, selected_label: str, state: dict, hidden: bool = False) -> dict:
    choice = get_choice_by_label(event, selected_label)
    choice = apply_ally_bonus(state, choice)
    outcome = apply_choice_result(state, choice, hidden)

    risk_delta = choice.get("효과", {}).get("위험도", 0)
    if outcome["사망"]:
        narrative = choice["실패시서술"]
    elif risk_delta >= 18:
        narrative = choice["실패시서술"]
    else:
        narrative = choice["성공시서술"]

    return {
        "선택지": choice,
        "판정결과": outcome,
        "서사결과": narrative,
        "업데이트된상태": deepcopy(state),
    }
