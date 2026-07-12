#!/usr/bin/env python3
"""
main.py — Menu board entry point (framebuffer renderer).

No pygame, no SDL, no EGL, no GPU. Renders with Pillow, writes to /dev/fb0.

Supports ROTATE=90 (or 270) in /etc/celtech/env for a portrait TV: the board
renders at the swapped canvas size and framebuffer.py rotates the finished
image onto the panel's native landscape buffer.
"""
import sys
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "common"))

from config import Config                          # noqa: E402
from api import ApiPoller                          # noqa: E402
from framebuffer import Framebuffer, hide_cursor   # noqa: E402
from menu_board import MenuBoard                   # noqa: E402


def group_sections(items):
    """MenuItemView[] -> sections, ordered by the backend's sortOrder."""
    by = {}
    for it in items or []:
        cid = it.get("categoryId") or it.get("categoryName") or "_"
        sec = by.setdefault(cid, {
            "categoryId": cid,
            "categoryName": it.get("categoryName") or "",
            "sortOrder": it.get("sortOrder", 0),
            "items": [],
        })
        sec["items"].append(it)
    secs = list(by.values())
    for s in secs:
        s["items"].sort(key=lambda i: (i.get("sortOrder", 0), i.get("name", "")))
        s["sortOrder"] = min((i.get("sortOrder", 0) for i in s["items"]), default=0)
    secs.sort(key=lambda s: (s["sortOrder"], s["categoryName"]))
    return secs


def main():
    cfg = Config(role="menu")
    for p in cfg.validate():
        print(f"CONFIG ERROR: {p}", file=sys.stderr)

    hide_cursor()
    fb = Framebuffer(rotate=cfg.rotate)
    cw, ch = fb.canvas_size
    print(f"framebuffer: {fb.width}x{fb.height} @ {fb.bpp}bpp "
          f"(stride {fb.stride}) rotate={fb.rotate} canvas={cw}x{ch}", flush=True)

    board = MenuBoard((cw, ch), title=cfg.board_title)
    poller = ApiPoller(cfg)
    poller.start()

    try:
        while True:
            fb.show(board.render(group_sections(poller.data or []),
                                 poller.online, time.time()))
            time.sleep(1.0)          # static content; 1 FPS is plenty
    except KeyboardInterrupt:
        pass
    finally:
        poller.stop()
        fb.close()


if __name__ == "__main__":
    main()
