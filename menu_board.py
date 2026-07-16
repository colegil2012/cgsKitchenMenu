"""
menu_board.py — customer Menu board, rendered with Pillow.

Same design as the Vue board; only the drawing primitives changed (SDL cannot
reach the screen on this hardware — see framebuffer.py).

  layout   two-column editorial; categories by sortOrder
  item     name [badge] ........ $price  / description / option lines
  86'd     item dimmed, name+price STRUCK THROUGH, "SOLD OUT" tag,
           badge and options hidden
  86'd     choice stays in its option line, struck through
"""
import os
from PIL import Image, ImageDraw, ImageFont

BG      = (0x0e, 0x25, 0x0e)
INK     = (0xf4, 0xee, 0xe0)
INK_DIM = (0xb3, 0xa8, 0x92)
ACCENT  = (0xd6, 0xb2, 0x7a)
SOLDOUT = (0xc0, 0x56, 0x3f)
RULE    = (0x4a, 0x50, 0x3c)
DOTS    = (0x44, 0x4c, 0x3e)

BADGE = {
    "gold":  (0xe0, 0xb6, 0x4a),
    "grass": (0x7b, 0xbf, 0x6a),
    "sea":   (0x5f, 0xb3, 0xc4),
}

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSET_DIR, "logo.png")


# ---- format.ts port ----------------------------------------------------
def cents_to_dollars(cents):
    if not isinstance(cents, (int, float)):
        return "—"
    d = cents / 100.0
    return f"${int(d)}" if float(d).is_integer() else f"${d:.2f}"


def display_price(item):
    return item.get("priceDisplay") or cents_to_dollars(item.get("priceCents"))


def choice_delta(c):
    d = c.get("priceDeltaCents") or 0
    if not d:
        return ""
    a = cents_to_dollars(abs(d))
    return f"+{a}" if d > 0 else f"-{a}"


def _dim(color, f=0.42):
    return tuple(int(c * f) for c in color)


class MenuBoard:
    def __init__(self, size, title="Menu"):
        self.w, self.h = size
        self.title = title
        s = max(self.h / 1080.0, 0.78)
        self.s = s

        def F(px):
            return ImageFont.truetype(os.path.join(FONT_DIR, "Fraunces.ttf"),
                                      max(10, int(px * s)))

        def N(px):
            return ImageFont.truetype(os.path.join(FONT_DIR, "NunitoSans.ttf"),
                                      max(9, int(px * s)))

        self.f_title   = F(25)
        self.f_section = F(20)
        self.f_item    = N(15)
        self.f_price   = F(12)
        self.f_desc    = N(9)
        self.f_opt     = N(10)
        self.f_badge   = N(6)
        self.f_status  = N(10)
        self.pad = int(24 * s)

        self.logo = None
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).convert("RGBA")
            target_h = int(120 * s)
            ratio = target_h / logo.height
            self.logo = logo.resize(
                (max(1, int(logo.width * ratio)), target_h), Image.LANCZOS)

    def _tw(self, d, f, t):
        return d.textbbox((0, 0), str(t), font=f)[2]

    def _th(self, f):
        a, de = f.getmetrics()
        return a + de

    def _wrap(self, d, f, text, max_w):
        words, lines, cur = str(text).split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if self._tw(d, f, t) <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _strike(self, d, x, y, f, text, color):
        w = self._tw(d, f, text)
        ly = y + self._th(f) // 2
        d.line([x, ly, x + w, ly], fill=color, width=max(1, int(2 * self.s)))

    def _pill(self, d, x, y, text, color):
        s = self.s
        f = self.f_badge
        tw = self._tw(d, f, text.upper())
        th = self._th(f)
        px, py = int(6 * s), int(2 * s)
        w, h = tw + px * 2, th + py * 2
        d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                            outline=color, width=max(1, int(1 * s)))
        d.text((x + px, y + py), text.upper(), font=f, fill=color)
        return w

    def _dotted(self, d, x1, x2, y):
        step = int(6 * self.s)
        r = max(1, int(1.2 * self.s))
        x = x1
        while x < x2:
            d.ellipse([x, y - r, x + r, y + r], fill=DOTS)
            x += step

    def _optline_text(self, g):
        parts = []
        for c in g.get("choices") or []:
            dd = choice_delta(c)
            parts.append(c.get("label", "") + (f" {dd}" if dd else ""))
        return f"{g.get('label','')}: " + ", ".join(parts)

    def _item_height(self, d, item, col_w):
        s = self.s
        h = self._th(self.f_item) + int(4 * s)
        if item.get("description"):
            h += len(self._wrap(d, self.f_desc, item["description"], int(col_w * .92))) \
                 * (self._th(self.f_desc) + int(1 * s))
        if item.get("available", True):
            for g in item.get("optionGroups") or []:
                if g.get("choices"):
                    h += len(self._wrap(d, self.f_opt, self._optline_text(g),
                                        int(col_w * .94))) \
                         * (self._th(self.f_opt) + int(1 * s))
        return h + int(12 * s)

    def _draw_item(self, d, item, x, y, col_w):
        s = self.s
        out = not item.get("available", True)
        ink = _dim(INK) if out else INK
        acc = _dim(ACCENT) if out else ACCENT
        dim = _dim(INK_DIM) if out else INK_DIM

        name = item.get("name", "")
        d.text((x, y), name, font=self.f_item, fill=ink)
        if out:
            self._strike(d, x, y, self.f_item, name, ink)
        cur = x + self._tw(d, self.f_item, name) + int(7 * s)

        if out:
            cur += self._pill(d, cur, y + int(4 * s), "Sold out", SOLDOUT) + int(5 * s)
        elif item.get("badgeLabel"):
            bc = BADGE.get(str(item.get("badgeColor") or "").lower(), INK_DIM)
            cur += self._pill(d, cur, y + int(4 * s), item["badgeLabel"], bc) + int(5 * s)

        price = display_price(item)
        pw = self._tw(d, self.f_price, price)
        px = x + col_w - pw
        d.text((px, y), price, font=self.f_price, fill=acc)
        if out:
            self._strike(d, px, y, self.f_price, price, acc)

        if px - cur > int(10 * s):
            self._dotted(d, cur, px - int(6 * s), y + int(self._th(self.f_item) * .62))

        cy = y + self._th(self.f_item) + int(4 * s)

        if item.get("description"):
            for ln in self._wrap(d, self.f_desc, item["description"], int(col_w * .92)):
                d.text((x, cy), ln, font=self.f_desc, fill=dim)
                cy += self._th(self.f_desc) + int(1 * s)

        if not out:
            for g in item.get("optionGroups") or []:
                if g.get("choices"):
                    cy = self._draw_optline(d, g, x, cy, col_w)

    def _draw_optline(self, d, g, x, y, col_w):
        s = self.s
        max_w = int(col_w * .94)
        gout = (not g.get("available", True)) or \
               all(not c.get("available", True) for c in g.get("choices") or [])

        cx, cy = x, y
        gl = f"{g.get('label','')}:"
        gc = _dim(ACCENT, .55) if gout else ACCENT
        d.text((cx, cy), gl, font=self.f_opt, fill=gc)
        if gout:
            self._strike(d, cx, cy, self.f_opt, gl, gc)
        cx += self._tw(d, self.f_opt, gl) + int(5 * s)

        chs = g.get("choices") or []
        for i, c in enumerate(chs):
            cout = not c.get("available", True)
            lab = c.get("label", "")
            dd = choice_delta(c)
            sep = ", " if i < len(chs) - 1 else ""
            piece = lab + (f" {dd}" if dd else "") + sep

            if cx + self._tw(d, self.f_opt, piece) > x + max_w:
                cx = x
                cy += self._th(self.f_opt) + int(1 * s)

            col = _dim(INK_DIM, .55) if cout else INK_DIM
            d.text((cx, cy), lab, font=self.f_opt, fill=col)
            if cout:
                self._strike(d, cx, cy, self.f_opt, lab, col)
            cx += self._tw(d, self.f_opt, lab)

            if dd:
                dc = _dim(INK, .55) if cout else INK
                t = f" {dd}"
                d.text((cx, cy), t, font=self.f_opt, fill=dc)
                if cout:
                    self._strike(d, cx, cy, self.f_opt, t, dc)
                cx += self._tw(d, self.f_opt, t)
            if sep:
                d.text((cx, cy), sep, font=self.f_opt, fill=INK_DIM)
                cx += self._tw(d, self.f_opt, sep)

        return cy + self._th(self.f_opt) + int(1 * s)

    def _section_height(self, d, sec, col_w):
        h = self._th(self.f_section) + int(14 * self.s)
        for it in sec["items"]:
            h += self._item_height(d, it, col_w)
        return h + int(22 * self.s)

    def render(self, sections, online, now_ts):
        img = Image.new("RGB", (self.w, self.h), BG)
        d = ImageDraw.Draw(img)
        s = self.s

        tx, ty = self.pad, int(14 * s)
        # centered header logo
        head_top = int(18 * s)
        if self.logo:
            lx = (self.w - self.logo.width) // 2
            img.paste(self.logo, (lx, head_top), self.logo)
            head_bottom = head_top + self.logo.height
        else:
            # fallback: centered title text if the logo is missing
            tw = self._tw(d, self.f_title, self.title)
            d.text(((self.w - tw) // 2, head_top), self.title,
                   font=self.f_title, fill=ACCENT)
            head_bottom = head_top + self._th(self.f_title)

        if not online:
            t = "reconnecting…"
            d.text((self.w - self.pad - self._tw(d, self.f_status, t), int(18 * s)),
                   t, font=self.f_status, fill=_dim(INK_DIM, .8))

        top = head_bottom + int(20 * s)
        gap = int(40 * s)
        col_w = (self.w - self.pad * 2 - gap) // 2
        cols = [self.pad, self.pad + col_w + gap]

        hs = [self._section_height(d, sec, col_w) for sec in sections]
        target = sum(hs) / 2.0
        split, run = len(sections), 0.0
        for i, hh in enumerate(hs):
            if run + hh / 2 > target:
                split = i
                break
            run += hh

        for ci, bucket in enumerate([sections[:split], sections[split:]]):
            x, y = cols[ci], top
            for sec in bucket:
                if y + self._th(self.f_section) > self.h - int(20 * s):
                    break
                d.text((x, y), sec["categoryName"], font=self.f_section, fill=ACCENT)
                uy = y + self._th(self.f_section) + int(4 * s)
                d.rectangle([x, uy, x + col_w, uy + max(1, int(2 * s))], fill=RULE)
                y = uy + int(12 * s)
                for it in sec["items"]:
                    ih = self._item_height(d, it, col_w)
                    if y + ih > self.h - int(16 * s):
                        break
                    self._draw_item(d, it, x, y, col_w)
                    y += ih
                y += int(18 * s)

        return img
