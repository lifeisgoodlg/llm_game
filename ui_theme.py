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
