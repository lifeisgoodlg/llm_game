import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Song+Myung&family=Nanum+Myeongjo:wght@400;700;800&display=swap');

/* 조선 단청 팔레트.
   궁궐 단청의 바탕색은 금이 아니라 뇌록(磊碌)이라는 청록이고,
   붉은색은 화려한 주홍이 아니라 주칠(朱漆)의 어두운 벽돌빛이다. */
:root {
    --noerok: #4fa896;
    --noerok-light: #7ec9b8;
    --noerok-deep: #2f6b60;
    --juchil: #c8503f;
    --meok: #0d1719;
    --panel: #122023;
    --hanji: #e4ddc9;
    --hanji-dim: #8fa39f;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background:
        radial-gradient(circle at 50% -10%, #16282b 0%, #0d1719 55%, #070f10 100%);
    color: var(--hanji);
    font-family: 'Nanum Myeongjo', serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stAppDeployButton"] {
    display: none;
}

[data-testid="stAppViewContainer"] ::-webkit-scrollbar {
    width: 10px;
}
[data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb {
    background: var(--noerok-deep);
    border-radius: 6px;
}
[data-testid="stAppViewContainer"] ::-webkit-scrollbar-track {
    background: var(--meok);
}

/* ---- Headings ---- */
[data-testid="stHeading"] h1 {
    font-family: 'Song Myung', serif;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .9rem;
    text-align: center;
    font-size: 2.15rem;
    letter-spacing: .04em;
    background: linear-gradient(180deg, var(--noerok-light), var(--noerok-deep));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    filter: drop-shadow(0 2px 10px rgba(79, 168, 150, .3));
    margin-bottom: .3rem;
}
[data-testid="stHeading"] h1::before,
[data-testid="stHeading"] h1::after {
    content: '';
    height: 1px;
    width: 36px;
    background: linear-gradient(90deg, transparent, var(--noerok));
    flex-shrink: 0;
}
[data-testid="stHeading"] h1::after {
    background: linear-gradient(90deg, var(--noerok), transparent);
}

[data-testid="stHeading"] h2,
[data-testid="stHeading"] h3 {
    font-family: 'Nanum Myeongjo', serif;
    font-weight: 800;
    color: var(--noerok-light);
    letter-spacing: .02em;
    border-left: 3px solid var(--juchil);
    padding-left: .6rem;
}

[data-testid="stCaptionContainer"] {
    color: var(--hanji-dim) !important;
    font-style: italic;
}

/* ---- Ornamental divider ---- */
hr {
    border: none;
    height: 1px;
    margin: 1.6rem 0;
    position: relative;
    background: linear-gradient(90deg, transparent, var(--noerok-deep) 15%, var(--noerok-deep) 85%, transparent);
}
hr::before {
    content: '❖';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-size: .8rem;
    color: var(--noerok-light);
}

/* ---- Buttons ---- */
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button {
    font-family: 'Nanum Myeongjo', serif;
    font-weight: 700;
    border-radius: 6px;
    transition: all .15s ease;
}
button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(160deg, var(--noerok-light), var(--noerok-deep));
    color: #08191a;
    border: 1px solid var(--noerok-deep);
    box-shadow: 0 2px 10px rgba(79, 168, 150, .35);
}
button[data-testid="stBaseButton-primary"]:hover {
    filter: brightness(1.08);
    box-shadow: 0 4px 18px rgba(79, 168, 150, .55);
    transform: translateY(-1px);
}
button[data-testid="stBaseButton-secondary"] {
    background: linear-gradient(160deg, #16292c, #0e1a1c);
    color: var(--hanji);
    border: 1px solid var(--noerok-deep);
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--noerok);
    color: var(--noerok-light);
    box-shadow: 0 0 14px rgba(79, 168, 150, .25);
    transform: translateY(-1px);
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #122023 0%, #0d1719 100%);
    border-right: 1px solid var(--noerok-deep);
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1.5rem;
}

/* ---- Metrics ---- */
[data-testid="stMetric"] {
    background: rgba(79, 168, 150, .08);
    border: 1px solid var(--noerok-deep);
    border-radius: 8px;
    padding: .6rem .4rem;
    text-align: center;
}
[data-testid="stMetricLabel"] {
    color: var(--hanji-dim) !important;
}
[data-testid="stMetricValue"] {
    color: var(--noerok-light) !important;
    font-family: 'Nanum Myeongjo', serif;
}

/* ---- Progress bar ---- */
[data-testid="stProgress"] div[role="progressbar"] > div > div {
    background: rgba(255, 255, 255, .08) !important;
}
[data-testid="stProgress"] div[role="progressbar"] > div > div > div {
    background: linear-gradient(90deg, var(--juchil), var(--noerok)) !important;
}

/* ---- Alerts ---- */
[data-testid="stAlertContainer"] {
    font-family: 'Nanum Myeongjo', serif;
    background: rgba(18, 32, 35, .75) !important;
    border-radius: 8px;
    border: 1px solid var(--noerok-deep);
}
[data-testid="stAlertContainer"] p {
    color: var(--hanji) !important;
}

/* ---- Chat messages ---- */
[data-testid="stChatMessage"] {
    background: rgba(18, 32, 35, .6);
    border: 1px solid var(--noerok-deep);
    border-radius: 10px;
    padding: .5rem .75rem;
}

/* ---- Inputs ---- */
[data-testid="stTextInput"] input,
[data-testid="stChatInput"] textarea {
    background: var(--panel) !important;
    color: var(--hanji) !important;
    border: 1px solid var(--noerok-deep) !important;
    font-family: 'Nanum Myeongjo', serif;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--noerok) !important;
    box-shadow: 0 0 0 1px var(--noerok) !important;
}

/* ---- Custom stat plate ---- */
.stat-plate {
    border: 1px solid var(--noerok-deep);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    background: linear-gradient(160deg, rgba(79, 168, 150, .10), rgba(13, 23, 25, .6));
    box-shadow: inset 0 0 0 1px rgba(79, 168, 150, .12);
    margin-bottom: .5rem;
}
.stat-plate-top {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: .7rem;
}
.stat-plate-name {
    font-family: 'Song Myung', serif;
    font-size: 1.3rem;
    color: var(--noerok-light);
}
.stat-plate-rank {
    font-family: 'Nanum Myeongjo', serif;
    font-weight: 800;
    font-size: 1.05rem;
    color: var(--hanji);
    background: rgba(79, 168, 150, .15);
    border: 1px solid var(--noerok-deep);
    border-radius: 999px;
    padding: .15rem .9rem;
}
.stat-plate-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: .6rem;
}
.stat-item {
    text-align: center;
    border-left: 1px solid rgba(79, 168, 150, .25);
    display: flex;
    flex-direction: column;
    gap: .15rem;
}
.stat-item:first-child {
    border-left: none;
}
.stat-label {
    font-size: .78rem;
    color: var(--hanji-dim);
    letter-spacing: .05em;
}
.stat-value {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--noerok-light);
}
.stat-value.danger {
    color: #e0705c;
}

/* ---- 단청 창살 문양 ----
   조선 궁궐 완자살(卍字) 창살을 옅게 깔아 글자만 있는 화면을 면한다. */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    opacity: .035;
    background-image:
        repeating-linear-gradient(0deg, var(--noerok) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(90deg, var(--noerok) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(0deg, var(--juchil) 0 1px, transparent 1px 132px),
        repeating-linear-gradient(90deg, var(--juchil) 0 1px, transparent 1px 132px);
}
[data-testid="stAppViewContainer"] > * {
    position: relative;
    z-index: 1;
}

/* ---- 사이드바 제목 ----
   본문 h1 은 장식선과 큰 글씨가 붙어 있어 사이드바에서 줄바꿈이 난다. */
section[data-testid="stSidebar"] [data-testid="stHeading"] h1 {
    display: block;
    text-align: left;
    font-size: 1.02rem;
    letter-spacing: .01em;
    margin-bottom: .1rem;
    filter: none;
}
section[data-testid="stSidebar"] [data-testid="stHeading"] h1::before,
section[data-testid="stSidebar"] [data-testid="stHeading"] h1::after {
    display: none;
}
section[data-testid="stSidebar"] [data-testid="stHeading"] h3 {
    font-size: .95rem;
}

/* ---- 품계 사다리 ---- */
.rank-ladder {
    display: flex;
    align-items: flex-start;
    overflow-x: auto;
    padding: .1rem 0 .35rem;
    margin-bottom: .2rem;
}
.rank-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: .3rem;
    flex: 0 0 auto;
}
.rank-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    border: 1px solid var(--noerok-deep);
    background: transparent;
}
.rank-step.done .rank-dot {
    background: var(--noerok-deep);
}
.rank-step.current .rank-dot {
    width: 13px;
    height: 13px;
    background: var(--noerok-light);
    border-color: var(--noerok-light);
    box-shadow: 0 0 0 3px rgba(79, 168, 150, .2);
    animation: rank-pulse 1.9s ease-in-out infinite;
}
@keyframes rank-pulse {
    0%, 100% { box-shadow: 0 0 0 3px rgba(79, 168, 150, .2); }
    50%      { box-shadow: 0 0 0 6px rgba(79, 168, 150, .05); }
}
@media (prefers-reduced-motion: reduce) {
    .rank-step.current .rank-dot { animation: none; }
}
.rank-label {
    font-size: .62rem;
    white-space: nowrap;
    color: var(--hanji-dim);
    letter-spacing: .02em;
}
.rank-step.done .rank-label { color: var(--hanji); }
.rank-step.current .rank-label {
    color: var(--noerok-light);
    font-weight: 800;
}
.rank-step.locked .rank-label { opacity: .45; }
.rank-link {
    flex: 1 1 auto;
    min-width: 10px;
    height: 1px;
    margin-top: 4px;
    background: var(--noerok-deep);
    opacity: .5;
}
.rank-link.locked { opacity: .22; }
/* 후궁은 중전이 될 수 없다. 그 국법을 점선으로 표시한다. */
.rank-link.gate {
    height: 0;
    border-top: 1px dashed var(--juchil);
    background: none;
    opacity: .85;
    min-width: 20px;
}
.rank-gate-note {
    font-size: .58rem;
    color: var(--juchil);
    text-align: right;
    letter-spacing: .04em;
    margin: -.15rem 0 .2rem;
    opacity: .8;
}

/* ---- 문안 촛불 ---- */
.candles {
    font-size: .95rem;
    letter-spacing: .12rem;
    line-height: 1.4;
    margin-bottom: .1rem;
}
.candles .out { opacity: .18; filter: grayscale(1); }
.candles-label {
    font-size: .68rem;
    color: var(--hanji-dim);
    font-style: italic;
}
</style>
"""


def inject_theme():
    st.markdown(_CSS, unsafe_allow_html=True)


def render_stat_plate(name: str, rank: str, love, power, danger):
    st.markdown(
        f"""
        <div class="stat-plate">
            <div class="stat-plate-top">
                <div class="stat-plate-name">🙋 {name}</div>
                <div class="stat-plate-rank">{rank}</div>
            </div>
            <div class="stat-plate-grid">
                <div class="stat-item">
                    <span class="stat-label">총애</span>
                    <span class="stat-value">{love}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">권세</span>
                    <span class="stat-value">{power}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">위험도</span>
                    <span class="stat-value danger">{danger}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rank_ladder(current_rank: str):
    """지나온 품계와 남은 품계, 그리고 국법이 막아선 지점을 한 줄로 보여준다."""
    from game_state import RANKS, safe_rank_index

    here = safe_rank_index(current_rank)
    parts = []

    for i, rank in enumerate(RANKS):
        if i:
            # 빈(정1품)과 중전 사이가 국법이 막아선 자리다
            gate = " gate" if RANKS[i] == "중전" else ""
            locked = " locked" if i > here and not gate else ""
            parts.append(f'<div class="rank-link{gate}{locked}"></div>')

        if i < here:
            state = "done"
        elif i == here:
            state = "current"
        else:
            state = "locked"
        parts.append(
            f'<div class="rank-step {state}">'
            f'<span class="rank-dot"></span>'
            f'<span class="rank-label">{rank}</span>'
            f"</div>"
        )

    st.markdown(
        '<div class="rank-ladder">' + "".join(parts) + "</div>"
        '<div class="rank-gate-note">점선 — 후궁은 중전이 될 수 없다는 국법</div>',
        unsafe_allow_html=True,
    )


def render_audience_candles(left: int, total: int):
    """남은 문안 횟수를 촛불로 보여준다. 쓴 만큼 꺼진다."""
    lit = "🕯️" * max(0, left)
    out = "".join(f'<span class="out">🕯️</span>' for _ in range(max(0, total - left)))
    st.markdown(
        f'<div class="candles">{lit}{out}</div>'
        f'<div class="candles-label">오늘의 문안 {left} / {total}회</div>',
        unsafe_allow_html=True,
    )
