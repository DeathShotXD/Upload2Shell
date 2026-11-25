#!/usr/bin/env python3
"""Render the demo GIF for the README in the repo's pixel-terminal colours.

The lines below are taken from a real run (Debian 13, Ubuntu 24.04, Ubuntu
22.04). Nothing here is made up. If you record your own screen capture, drop
that in at assets/demo.gif instead.

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

# Pixel-terminal palette (matches assets/banner.png + logo.png).
BG = (3, 7, 11)          # #03070B  base ink
PANEL = (7, 19, 25)      # #071319  device chrome
BAR = (12, 32, 39)       # #0C2027  title bar
EDGE = (30, 58, 66)      # #1E3A42  borders
BONE = (243, 230, 200)   # #F3E6C8  cream paper
DIM = (124, 147, 160)    # #7C93A0  muted
CYAN = (46, 230, 210)    # #2EE6D2  accent / prompt
ORANGE = (245, 135, 31)  # #F5871F  accent / status
AMBER = (248, 194, 74)   # #F8C24A  highlight
ROSE = (242, 109, 126)   # #F26D7E  control
GREEN = (126, 231, 135)  # #7EE787  terminal output

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT = ImageFont.truetype(MONO, 13)
FONT_S = ImageFont.truetype(MONO, 10)
FONT_T = ImageFont.truetype(MONO_B, 12)

LEFT = 60
TOP = 104
LH = 20

Segments = list[tuple[str, tuple[int, int, int]]]


def seg(*parts: tuple[str, tuple[int, int, int]]) -> Segments:
    return list(parts)


OUTPUT = [
    seg(("$ ", CYAN), ("python3 cups_poc.py -t 127.0.0.1:6310 -q u2s", BONE)),
    seg(("  target   127.0.0.1:6310/u2s", DIM)),
    seg(("  status   0x0000 (successful-ok)  HTTP 200", ORANGE)),
    seg(("$ ", CYAN), ("docker exec u2s-pwn cat /tmp/pwned", BONE)),
    seg(("uid=7(lp) gid=7(lp) groups=7(lp)", GREEN)),
    seg(("", DIM)),
    seg(("debian13    run 1-3  -> uid=7(lp)", BONE)),
    seg(("ubuntu24.04 run 1-3  -> uid=7(lp)", BONE)),
    seg(("ubuntu22.04 run 1-3  -> uid=7(lp)", BONE)),
    seg(("[+] 9/9 anonymous IPP jobs executed", AMBER)),
]


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # faint pixel grid
    for gx in range(0, W, 22):
        d.line([gx, 0, gx, H], fill=(10, 20, 26))
    for gy in range(0, H, 22):
        d.line([0, gy, W, gy], fill=(10, 20, 26))
    # window
    d.rounded_rectangle([24, 24, W - 24, H - 24], radius=10, fill=PANEL,
                        outline=EDGE, width=1)
    d.rectangle([25, 25, W - 25, 70], fill=BAR)
    d.line([24, 70, W - 24, 70], fill=EDGE)
    for i, c in enumerate((ROSE, AMBER, CYAN)):
        d.ellipse([52 + i * 22, 42, 62 + i * 22, 52], fill=c)
    d.text((126, 40), "upload2shell / lab", font=FONT_T, fill=DIM)
    d.text((W - 52, 40), "AUTHORIZED LAB", font=FONT_T, fill=ORANGE, anchor="ra")
    d.line([24, H - 50, W - 24, H - 50], fill=EDGE)
    d.text((60, H - 36), "real run / debian 13 + ubuntu 22.04 + ubuntu 24.04",
           font=FONT_S, fill=DIM)
    d.text((W - 52, H - 36), "github.com/DeathShotXD/Upload2Shell",
           font=FONT_S, fill=DIM, anchor="ra")
    # pixel accents
    d.rectangle([24, 24, 28, H - 24], fill=CYAN)
    d.rectangle([28, 24, 32, H - 24], fill=(20, 120, 112))
    d.rectangle([W - 32, 24, W - 24, H - 24], fill=(8, 14, 18))
    for i in range(6):
        d.rectangle([60 + i * 16, 76, 60 + i * 16 + 8, 80],
                    fill=CYAN if i % 2 == 0 else ORANGE)
    d.rectangle([LEFT, TOP - 6, LEFT + 6, TOP], fill=ORANGE)
    d.rectangle([LEFT + 8, TOP - 6, LEFT + 12, TOP], fill=ORANGE)
    return im, d


def scanlines(im: Image.Image) -> Image.Image:
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, H, 3):
        d.line([0, y, W, y], fill=(0, 0, 0, 40))
    return im


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
        draw_line(d, y, seg(("$ ", CYAN), (typed[:typed_done], BONE)))
        if cursor:
            x = (LEFT + d.textlength("$ ", font=FONT)
                 + d.textlength(typed[:typed_done], font=FONT))
            d.rectangle([x + 1, y + 1, x + 8, y + 15], fill=CYAN)
    elif cursor:
        d.rectangle([LEFT, y + 1, LEFT + 7, y + 15], fill=CYAN)
    return scanlines(im)


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
    lines.append(seg(("$ ", CYAN), (text, BONE)))
    hold(3)

    for item in OUTPUT[1:]:
        lines.append(item)
        hold(3)
        if item[0][0].startswith("[+] 9/9"):
            hold(12)

    hold(40)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    flat = frames[-1].quantize(colors=48, method=Image.MEDIANCUT)
    pal = [im.quantize(palette=flat, dither=Image.NONE) for im in frames]
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=FRAME,
                loop=0, optimize=True, disposal=2)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KiB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
