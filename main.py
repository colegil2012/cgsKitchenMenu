#!/usr/bin/env python3
"""main.py — Menu board entry point (framebuffer renderer). No pygame/SDL/GPU."""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "common"))
from config import Config
from api import ApiPoller
from framebuffer import Framebuffer, hide_cursor
from menu_board import MenuBoard


def group_sections(items):
    by = {}
    for it in items or []:
        cid = it.get("categoryId") or it.get("categoryName") or "_"
        sec = by.setdefault(cid, {"categoryId": cid,
                                  "categoryName": it.get("categoryName") or "",
                                  "sortOrder": it.get("sortOrder", 0), "items": []})
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
    fb = Framebuffer()
    print(f"framebuffer: {fb.width}x{fb.height} @ {fb.bpp}bpp", flush=True)
    board = MenuBoard((fb.width, fb.height), title=cfg.board_title)
    poller = ApiPoller(cfg)
    poller.start()
    try:
        while True:
            fb.show(board.render(group_sections(poller.data or []),
                                 poller.online, time.time()))
            time.sleep(1.0)      # static content
    except KeyboardInterrupt:
        pass
    finally:
        poller.stop(); fb.close()


if __name__ == "__main__":
    main()
