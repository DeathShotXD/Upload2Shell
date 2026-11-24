#!/usr/bin/env python3
"""Render a terminal-style GIF from the real Upload2Shell lab output.

Lines are copied from an actual run (Debian 13, Ubuntu 24.04, Ubuntu 22.04).
No output is invented.

    python3 scripts/make_demo.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "demo.gif"

W, H = 960, 560
FPS = 12
FRAME = int(1000 / FPS)

BG = (5, 9, 12)
PANEL = (8, 15, 19)
BAR = (12, 26, 32)
BONE = (233, 242, 245)
DIM = (127, 149, 168)
TEAL = (94, 234, 212)
AMBER = (245, 199, 106)
ROSE = (251, 113, 133)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT = ImageFont.truetype(MONO, 13)
FONT_S = ImageFont.truetype(MONO, 10)
FONT_T = ImageFont.truetype(MONO_B, 12)

LEFT = 52
TOP = 100
LH = 20

Segments = list[tuple[str, tuple[int, int, int]]]


def seg(*parts: tuple[str, tuple[int, int, int]]) -> Segments:
    return list(parts)


OUTPUT = [
    seg(("$ ", TEAL), ("python3 cups_poc.py -t 127.0.0.1:6310 -q u2s", BONE)),
    seg(("  target   127.0.0.1:6310/u2s", DIM)),
    seg(("  status   0x0000 (successful-ok)  HTTP 200", AMBER)),
    seg(("$ ", TEAL), ("docker exec u2s-pwn cat /tmp/pwned", BONE)),
    seg(("uid=7(lp) gid=7(lp) groups=7(lp)", TEAL)),
    seg(("", DIM)),
    seg(("debian13    run 1-3  -> uid=7(lp)", BONE)),
    seg(("ubuntu24.04 run 1-3  -> uid=7(lp)", BONE)),
    seg(("ubuntu22.04 run 1-3  -> uid=7(lp)", BONE)),
    seg(("[+] 9/9 anonymous IPP jobs executed", AMBER)),
]


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([24, 24, W - 24, H - 24], radius=12, fill=PANEL,
                        outline=(29, 47, 57), width=1)
    d.rectangle([25, 25, W - 25, 70], fill=BAR)
    d.line([24, 70, W - 24, 70], fill=(29, 47, 57))
    for i, c in enumerate((ROSE, AMBER, TEAL)):
        d.ellipse([52 + i * 22, 42, 62 + i * 22, 52], fill=c)
    d.text((126, 40), "upload2shell / lab", font=FONT_T, fill=DIM)
    d.text((W - 52, 40), "AUTHORIZED LAB", font=FONT_T, fill=AMBER, anchor="ra")
    d.line([24, H - 50, W - 24, H - 50], fill=(29, 47, 57))
    d.text((52, H - 36), "real run / debian 13 + ubuntu 22.04 + ubuntu 24.04",
           font=FONT_S, fill=DIM)
    d.text((W - 52, H - 36), "github.com/DeathShotXD/Upload2Shell",
           font=FONT_S, fill=DIM, anchor="ra")
    return im, d


def draw_line(d: ImageDraw.ImageDraw, y: int, parts: Segments) -> None:
    x = LEFT
    for text, colour in parts:
        d.text((x, y), text, font=FONT, fill=colour)
        x += d.textlength(text, font=FONT)


def render(lines: list[Segments], typed: str | None = None,
           typed_done: int = 0, cursor: bool = True) -> Image.Image:
    im, d = base()
    y = TOP
    for parts in lines:
        draw_line(d, y, parts)
        y += LH
    if typed is not None:
        draw_line(d, y, seg(("$ ", TEAL), (typed[:typed_done], BONE)))
        if cursor:
            x = (LEFT + d.textlength("$ ", font=FONT)
                 + d.textlength(typed[:typed_done], font=FONT))
            d.rectangle([x + 1, y + 1, x + 8, y + 15], fill=TEAL)
    elif cursor:
        d.rectangle([LEFT, y + 1, LEFT + 7, y + 15], fill=TEAL)
    return im


def main() -> None:
    frames: list[Image.Image] = []
    lines: list[Segments] = []

    def hold(n: int = 3) -> None:
        for _ in range(n):
            frames.append(render(lines, cursor=False))

    hold(10)
    text = "python3 cups_poc.py -t 127.0.0.1:6310 -q u2s"
    for i in range(0, len(text) + 1, 3):
        frames.append(render(lines, typed=text, typed_done=i))
    lines.append(seg(("$ ", TEAL), (text, BONE)))
    hold(3)

    for item in OUTPUT[1:]:
        lines.append(item)
        hold(3)
        if item[0][0].startswith("[+] 9/9"):
            hold(12)

    hold(40)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    flat = frames[-1].quantize(colors=32, method=Image.MEDIANCUT)
    pal = [im.quantize(palette=flat, dither=Image.NONE) for im in frames]
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=FRAME,
                loop=0, optimize=True, disposal=2)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KiB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
