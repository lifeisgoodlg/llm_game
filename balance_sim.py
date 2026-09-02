"""승급/강등 수치 밸런스 시뮬레이터.

LLM 없이, story_llm.py 프롬프트에 선언된 효과 범위에서 무작위 표본을 뽑아
수천 판을 돌려 엔딩 분포를 본다. 실제 game_state.py 로직을 그대로 호출하므로
곡선 노브를 바꾸면 결과가 바로 반영된다.

    python balance_sim.py           정책별 엔딩 분포
    python balance_sim.py --tune    목표 분포에 맞는 난이도 배율 탐색
"""
import random
import sys
from collections import Counter

import game_state as gs

# story_llm.py 의 [효과 수치 가이드] 와 동일
EFFECT_RANGES = {
    "strategic": {"총애": (-5, 20), "권세": (-5, 18), "위험도": (-10, 15)},
    "safe":      {"총애": (-3, 12), "권세": (-3, 10), "위험도": (-15, 5)},
    "gamble":    {"총애": (-15, 35), "권세": (-10, 30), "위험도": (-5, 35)},
}
RELATION_KEYS = ["왕", "대비", "중전", "상궁", "경쟁후궁", "우호후궁", "영의정"]

MAIN_STAGES = 10
HIDDEN_STAGES = 3
FATAL_THRESHOLD = 100     # 프롬프트 템플릿이 내보내는 사망위험임계치

ENDINGS = [
    gs.ENDING_DEATH,
    gs.ENDING_QUEEN,
    gs.ENDING_PURGED,
    gs.ENDING_THRONE,
    gs.ENDING_FOUND,
]

# 정책: (선택지 성향, 문안 대상 성향)
POLICIES = ["안전형", "균형형", "명분형", "힘형", "야심형"]


def make_choice(choice_id, rng):
    ranges = EFFECT_RANGES[choice_id]
    effect = {stat: rng.randint(lo, hi) for stat, (lo, hi) in ranges.items()}
    # LLM 은 관계변화를 대부분 0으로 두고 일부만 채운다
    effect["관계변화"] = {
        k: (0 if rng.random() < 0.55 else rng.randint(-10, 10)) for k in RELATION_KEYS
    }
    return {
        "choice_id": choice_id,
        "효과": effect,
        "직접사망가능": choice_id == "gamble",
        "사망위험임계치": FATAL_THRESHOLD,
    }


def pick_choice(policy, state, rng):
    if policy == "안전형":
        return "safe"
    if policy == "야심형":
        return "gamble"
    if policy == "명분형":
        # 위험도를 낮게 유지해야 즉위 관문을 통과한다
        return "safe" if state["위험도"] >= 55 else "strategic"
    if policy == "힘형":
        # 권세를 최대한 끌어올린다. 위험도는 죽지 않을 만큼만 감수한다.
        return "gamble" if state["위험도"] < 62 else "strategic"
    return rng.choice(["strategic", "safe", "gamble"])


def pick_target(policy, state, rng):
    if policy == "균형형":
        return rng.choice(RELATION_KEYS)
    if policy == "명분형":
        # 왕의 호감으로 승급하고, 영의정을 얻어 즉위 루트를 연다
        req = gs.RANK_UP_REQUIREMENTS.get(state["현재품계"], {})
        if state["관계"]["왕"] < req.get("왕호감", 100):
            return "왕"
        if state["관계"]["영의정"] < gs.THRONE_GATE["영의정"]:
            return "영의정"
        return rng.choice(["상궁", "우호후궁"])
    # 나머지는 승급에 직결되는 왕만 본다 (영의정을 방치하므로 개국 루트로 간다)
    req = gs.RANK_UP_REQUIREMENTS.get(state["현재품계"], {})
    if state["관계"]["왕"] < req.get("왕호감", 100):
        return "왕"
    return rng.choice(["상궁", "우호후궁", "경쟁후궁"])


def play(policy, rng, use_audience=True):
    state = gs.init_game_state({"초기품계": "숙원"}, {"경쟁후궁": {"성향": "적대적"}})
    hidden = False
    stage = 1

    while True:
        if use_audience:
            for _ in range(gs.AUDIENCE_PER_STAGE):
                gs.apply_relation_change(state, pick_target(policy, state, rng), rng.randint(-2, 7))

        choice = make_choice(pick_choice(policy, state, rng), rng)
        gs.apply_choice_result(state, choice, hidden)

        if not state["생존"]:
            return state["엔딩"], state
        if state["엔딩"] in (gs.ENDING_THRONE, gs.ENDING_FOUND):
            return state["엔딩"], state

        if state["현재품계"] == "중전" and not hidden:
            hidden = True
            gs.decide_route(state)
            stage = 0

        stage += 1
        if stage > (HIDDEN_STAGES if hidden else MAIN_STAGES):
            # game_logic.force_to_end_game 과 동일한 처리
            if hidden or state["현재품계"] == "중전":
                return gs.ENDING_QUEEN, state
            return gs.ENDING_DEATH, state


def run(policy, n, seed=0, use_audience=True):
    rng = random.Random(seed)
    endings = Counter()
    ranks = Counter()
    routes = Counter()
    for _ in range(n):
        ending, state = play(policy, rng, use_audience)
        endings[ending] += 1
        ranks[state["현재품계"]] += 1
        routes[state.get("루트") or "히든미도달"] += 1
    return endings, ranks, routes


def dist(endings, n):
    return [endings[e] / n for e in ENDINGS]


def report(n=3000):
    print("난이도 배율 %.2f / %d판" % (gs.DIFFICULTY, n))
    print()
    header = "%-8s%8s%8s%9s%8s%8s   %s" % (
        "정책", "사망", "중전", "폐위사사", "여왕", "개국", "루트 진입"
    )
    print(header)
    for policy in POLICIES:
        endings, _, routes = run(policy, n, seed=hash(policy) & 0xFFFF)
        d = dist(endings, n)
        route_txt = "즉위 %d%% / 개국 %d%%" % (
            routes[gs.ROUTE_THRONE] * 100 // n, routes[gs.ROUTE_FOUND] * 100 // n
        )
        print("%-8s%7.1f%%%7.1f%%%8.1f%%%7.1f%%%7.1f%%   %s" % (
            policy, d[0] * 100, d[1] * 100, d[2] * 100, d[3] * 100, d[4] * 100, route_txt
        ))

    print()
    endings, _, _ = run("균형형", n, seed=7, use_audience=False)
    d = dist(endings, n)
    print("참고: 균형형이 문안을 한 번도 안 했을 때  사망 %.1f%% / 중전 %.1f%% / 폐위 %.1f%% / 여왕 %.1f%% / 개국 %.1f%%"
          % (d[0] * 100, d[1] * 100, d[2] * 100, d[3] * 100, d[4] * 100))


def tune(target=(0.28, 0.32, 0.08, 0.20, 0.12), n=1500):
    """난이도 배율을 훑어 목표 엔딩 분포에 가장 가까운 값을 찾는다."""
    print("목표 분포  사망 %.0f%% / 중전 %.0f%% / 폐위 %.0f%% / 여왕 %.0f%% / 개국 %.0f%%"
          % tuple(t * 100 for t in target))
    print("기준 정책  균형형 (%d판)" % n)
    print()
    print("%8s%8s%8s%9s%8s%8s%9s" % ("난이도", "사망", "중전", "폐위사사", "여왕", "개국", "오차"))

    best = None
    for step in range(13):
        d = round(0.45 + step * 0.05, 2)
        gs.RANK_UP_REQUIREMENTS = gs.build_rank_requirements(d)
        endings, _, _ = run("균형형", n, seed=42)
        got = dist(endings, n)
        err = sum(abs(a - b) for a, b in zip(got, target))
        if best is None or err < best[0]:
            best = (err, d, got)
        print("%8.2f%7.1f%%%7.1f%%%8.1f%%%7.1f%%%7.1f%%%9.3f" % (
            d, got[0] * 100, got[1] * 100, got[2] * 100, got[3] * 100, got[4] * 100, err
        ))

    err, d, got = best
    print()
    print("=> 목표에 가장 가까운 DIFFICULTY = %.2f  (오차 %.3f)" % (d, err))
    print("   game_state.py 의 DIFFICULTY 를 이 값으로 바꾸세요.")


if __name__ == "__main__":
    if "--tune" in sys.argv:
        tune()
    else:
        report()
