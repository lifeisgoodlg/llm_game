"""장면 배경과 엔딩 일러스트를 한 번만 생성해 assets/ 에 저장한다.

게임 중에는 이미지를 만들지 않는다. 매 스테이지 생성하면 판당 비용이
텍스트의 열 배가 되고, 한 장에 십수 초가 붙고, 무엇보다 같은 장소가
매번 다르게 그려진다. 그래서 미리 뽑아 정적 파일로 둔다.

    python scripts/generate_assets.py            아직 없는 것만 생성
    python scripts/generate_assets.py --force    전부 다시 생성
    python scripts/generate_assets.py --only 옥좌 사약

배경은 글자 뒤에 깔리지만, 어둡게 만드는 일은 화면의 CSS 가 한다.
그래야 다시 뽑지 않고 조절할 수 있다. 이미지 자체는 건물이 보일 만큼
밝게 뽑고, 너무 어두우면 저장할 때 경고한다.
"""
import argparse
import base64
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parent.parent
BG_DIR = ROOT / "assets" / "bg"
ENDING_DIR = ROOT / "assets" / "ending"

MODEL = "gpt-image-1"
SIZE = "1536x1024"
QUALITY = "medium"

# 저장 규격. 배경은 글자 뒤에 깔리므로 크게 둘 이유가 없다.
MAX_WIDTH = 1280
WEBP_QUALITY = 72

# 어둡게 덮는 일은 CSS 가 한다. 원본이 이보다 어두우면 화면에서 아무것도
# 보이지 않으므로 경고한다. (0~255 평균 밝기)
MIN_MEAN_BRIGHTNESS = 30

# 모든 이미지가 한 세트로 보이도록 앞에 똑같이 붙이는 지시.
# 조선을 명시하지 않으면 중국풍이나 일본풍으로 흐른다.
STYLE = (
    "Korean Joseon dynasty palace scene, in the style of a moody traditional "
    "Korean ink-wash painting with muted color washes. "
    "Deep teal-green (dancheong noerok) and dark brick-red (juchil) accents. "
    "Moonlit night with warm lantern glow. Atmospheric but clearly legible: "
    "roof tiles, bracket sets and lattice doors must read plainly, with soft "
    "mid-tones and gentle highlights. Not pitch black, no crushed shadows. "
    "Wide cinematic composition with open space in the centre. "
    "Absolutely no people, no faces, no letters, no text, no signage, no watermark. "
    "This is Korean architecture, not Chinese and not Japanese: "
    "gently curved tiled roof, wooden lattice doors, stone terrace, paper windows. "
    "Scene: "
)

BACKGROUNDS = {
    "처소": "a small dim chamber of a low-ranking royal concubine, one guttering candle, "
            "a folded sleeping mat, wooden lattice door half open to a dark courtyard",
    "후원": "the rear garden of the palace at night, a still lotus pond, "
            "stone lantern, bare plum branches, thin mist over the water",
    "산실청": "the royal birthing chamber at deep night, folding screen, "
             "a brazier with dying embers, medicine bowl on a low table, white cloth",
    "정전": "the vast empty stone courtyard before the main throne hall, "
           "rows of rank stones receding into darkness, heavy roof silhouette against the sky",
    "교태전": "the queen's inner residence, a wide empty wooden floor, "
            "silk curtains drawn, a low writing desk, moonlight across the boards",
    "옥좌": "the royal throne hall interior seen from a distance, the empty throne "
           "beneath the Irworobongdo folding screen of sun, moon and five peaks",
}

ENDINGS = {
    "사망": "a snow-covered empty courtyard of an abandoned palace annex, "
          "one lantern fallen and extinguished in the snow, footprints already filling in",
    "폐위사사": "a single lacquered bowl of poison set on a red cloth on a bare wooden floor, "
             "a discarded royal seal ribbon beside it, cold grey dawn light",
    "중전엔딩": "the empty seat of the queen in her inner hall, ceremonial robes laid across it, "
             "a window open onto the distant throne hall she never reached",
    "여왕등극": "the royal throne occupied by a heavy ceremonial robe and crown, "
             "the Irworobongdo screen behind it lit by dawn, "
             "rows of empty officials' seats below, tense and grand",
    "개국": "the old royal ancestral shrine burning at night, its roof collapsing, "
          "a new uncarved stone tablet standing upright in the foreground, "
          "smoke and embers rising",
}


def save_webp(raw: bytes, path: Path):
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    if image.width > MAX_WIDTH:
        height = round(image.height * MAX_WIDTH / image.width)
        image = image.resize((MAX_WIDTH, height), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
    brightness = ImageStat.Stat(image.convert("L")).mean[0]
    return path.stat().st_size, brightness


def generate(client: OpenAI, name: str, scene: str, path: Path) -> bool:
    print(f"  {name} ... ", end="", flush=True)
    try:
        result = client.images.generate(
            model=MODEL,
            prompt=STYLE + scene,
            size=SIZE,
            quality=QUALITY,
            n=1,
        )
    except Exception as exc:
        print(f"실패: {exc}")
        return False

    item = result.data[0]
    if getattr(item, "b64_json", None):
        raw = base64.b64decode(item.b64_json)
    else:
        import urllib.request
        with urllib.request.urlopen(item.url) as response:
            raw = response.read()

    size, brightness = save_webp(raw, path)
    warning = "  ← 너무 어둡습니다. 다시 뽑으세요" if brightness < MIN_MEAN_BRIGHTNESS else ""
    print(f"저장 ({size // 1024}KB, 밝기 {brightness:.0f}/255){warning}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="이미 있는 것도 다시 생성")
    parser.add_argument("--only", nargs="*", help="이름을 지정해 일부만 생성")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY 가 없습니다. .env 를 확인하세요.")

    targets = []
    for name, scene in BACKGROUNDS.items():
        targets.append((name, scene, BG_DIR / f"{name}.webp"))
    for name, scene in ENDINGS.items():
        targets.append((name, scene, ENDING_DIR / f"{name}.webp"))

    if args.only:
        wanted = set(args.only)
        targets = [t for t in targets if t[0] in wanted]
        if not targets:
            sys.exit(f"이름을 찾을 수 없습니다: {', '.join(args.only)}")

    todo = [t for t in targets if args.force or not t[2].exists()]
    skipped = len(targets) - len(todo)

    if not todo:
        print(f"생성할 것이 없습니다. (이미 있음 {skipped}장)")
        return

    print(f"{MODEL} / {SIZE} / {QUALITY} 로 {len(todo)}장 생성합니다.", end="")
    print(f" (건너뜀 {skipped}장)" if skipped else "")

    done = sum(generate(OpenAI(), *t) for t in todo)
    print(f"\n완료: {done}/{len(todo)}장")


if __name__ == "__main__":
    main()
