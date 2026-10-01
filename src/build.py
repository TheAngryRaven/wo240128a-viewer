#!/usr/bin/env python3
"""
Build the WO240128A viewer pages from src/viewer.template.html + scad/WO240128A_240x128_COG.scad.

    python3 src/build.py            # writes index.html (offline, vendor/three.min.js)
                                    #    and wo240128a-3d.single.html (three.js from cdnjs)
                                    #    and build/artifact.html (no document skeleton, for claude.ai artifacts)

The template has two placeholders:
    __SCAD__       the OpenSCAD source, HTML-escaped, shown in the <pre> block
    __THREE_SRC__  where three.js r128 is loaded from
"""
import html
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TEMPLATE = HERE / "viewer.template.html"
SCAD = ROOT / "scad" / "WO240128A_240x128_COG.scad"

CDN_THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
LOCAL_THREE = "vendor/three.min.js"

SKELETON_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<style>
  :root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
  [hidden] { display: none !important; }
</style>
"""


LOGO = HERE / "logo_bitmaps.js"   # from make_logo.py


def render(three_src: str) -> str:
    tpl = TEMPLATE.read_text()
    scad = SCAD.read_text()
    logo = LOGO.read_text().strip() if LOGO.exists() else "const LOGO_SRC = { HI:{w:8,h:8,b64:'AAAAAAAAAAA='}, MID:{w:8,h:8,b64:'AAAAAAAAAAA='}, SM:{w:8,h:8,b64:'AAAAAAAAAAA='} };"
    return (tpl.replace("__SCAD__", html.escape(scad, quote=False))
               .replace("__THREE_SRC__", three_src)
               .replace("__LOGO_SRC__", logo))


def standalone(three_src: str) -> str:
    """Wrap the page in a full HTML document: everything up to </style> goes into <head>."""
    page = render(three_src)
    head, body = page.split("</style>", 1)
    return SKELETON_HEAD + head + "</style>\n</head>\n<body>" + body + "\n</body>\n</html>\n"


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(f"wrote {path.relative_to(ROOT)}  ({len(text) / 1024:.0f} KB)")


if __name__ == "__main__":
    write(ROOT / "index.html", standalone(LOCAL_THREE))
    write(ROOT / "wo240128a-3d.single.html", standalone(CDN_THREE))
    write(ROOT / "build" / "artifact.html", render(CDN_THREE))
