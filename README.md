# cgsKitchenMenu

Customer-facing menu board for the CGS Kitchen food truck. Runs on a **Raspberry Pi Zero 2 W** wired to an HDMI TV, and shows the live menu — prices, options, and what's 86'd — straight from the backend.

It is a read-only display. The truck controls the menu entirely from cgsKitchen; this board just reflects it.

---

## Architecture

**Python + Pillow, drawing straight to the Linux framebuffer (`/dev/fb0`).**

No browser. No compositor. No GPU. No Node.

```
cgsKitchen (Spring, DigitalOcean)
        │  GET /api/menu/all   [X-API-Key]
        ▼
   ApiPoller (background thread)
        │  MenuItemView[]
        ▼
   MenuBoard.render()  →  PIL.Image
        │
        ▼
   Framebuffer.show()  →  mmap → /dev/fb0  →  TV
```

### Why not a browser?

This board was originally a Vue app in Chromium. **On a 512MB Zero 2 W that does not work.** Chromium couldn't get a GPU context (`EGL_BAD_ATTRIBUTE`), fell back to software rendering, and exhausted the board — 84MB RAM free, swap 77% consumed, renderer at 143% CPU, network process pegged at 102% and wedged. Blank screen.

SDL/pygame was tried next and hits the same GPU wall (`EGL not initialized`), with no `fbcon` fallback compiled in.

The framebuffer works because it never touches the GPU: we `mmap` the kernel's buffer and write bytes; the display controller scans them out. Nothing to negotiate, nothing to fail.

---

## Layout

```
main.py             entry point: poll loop + framebuffer blit
menu_board.py       the renderer (sections, dotted leaders, 86 handling)
preview.py          dev tool — render to PNG instead of the framebuffer
common/
  config.py         reads /etc/celtech/env at RUNTIME
  api.py            background poller, last-known-good on drop
  framebuffer.py    mmap /dev/fb0, RGB565/BGRA packing, rotation
fonts/              vendored TTFs (Fraunces, Nunito Sans) — committed on purpose
deploy/
  cgs-menu.service  systemd unit
requirements.txt    Pillow + numpy. That's it.
update.sh           git pull + systemctl restart
```

---

## Configuration

All config lives in **`/etc/celtech/env`** on the device, read **at runtime** — change it and restart the service; there is no build step.

```ini
API_BASE_URL=https://celtechgs.kitchen
API_KEY=<the backend's API key>

# optional
POLL_SECONDS=30      # default 30 for menu (it changes rarely)
BOARD_TITLE=Menu     # heading text
ROTATE=90            # portrait — see below
```

`/etc/celtech/role` contains `menu`.

### Portrait mode

The menu board is usually mounted **portrait**. Set `ROTATE=90` (or `270`, depending which way you turned the TV) and physically rotate the screen.

Rotation is handled **entirely in software** — no kernel flags, no `config.txt` display settings. The board renders at the swapped canvas size (e.g. 768×1366 portrait) and `framebuffer.py` rotates the finished image onto the panel's native landscape buffer before blitting. The two-column layout rebalances automatically for the narrower canvas.

Preview it before you mount anything:

```bash
./preview.py menu --demo --rotate 90 --show
```

---

## What it renders

Two-column editorial layout. Categories in the backend's `sortOrder`; items within a category likewise. The truck controls the whole layout from cgsKitchen — nothing is configured per-device.

Each item shows its name, an optional badge (`Most Loved`, `New`, `Top Seller` — colored gold/grass/sea), a dotted leader, and the price. Below it: the description, then the option groups inline (`Cheese: Cheddar, Beer cheese +$1, No cheese`).

**86'd items** stay in place rather than vanishing — a hole in the menu is confusing, and customers ask about things that aren't there. Instead the item dims, the **name and price are struck through**, a `SOLD OUT` tag appears, and its badge and options are hidden.

**86'd choices** stay in their option line, struck through individually (`Cheese: Cheddar, ~~Beer cheese +$1~~, No cheese`), so customers can see the option exists but isn't available today.

**Prices** are integer cents on the wire; formatted at the edge (`1200 → $12`, `950 → $9.50`). The server's `priceDisplay` is preferred when present, otherwise formatted from `priceCents`.

**Connectivity**: on a network drop the board **keeps the last known menu on screen** rather than blanking, with a quiet `reconnecting…` note. A blank menu board loses sales; a slightly stale one doesn't.

---

## Running

### On the Pi

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py menu
```

It prints the panel geometry before drawing — proof it found the framebuffer:

```
framebuffer: 1366x768 @ 16bpp (stride 2732) rotate=90 canvas=768x1366
```

Then install the service:

```bash
sudo cp deploy/cgs-menu.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cgs-menu.service
```

The user must be in the **`video`** group (that's who owns `/dev/fb0`):

```bash
sudo usermod -aG video druid && sudo reboot
```

### On a dev laptop

`main.py` **will not run** on a desktop machine — the compositor owns `/dev/fb0` and you'll get `PermissionError`. That's correct, not a bug. Use `preview.py`, which runs the *same* renderer and writes a PNG:

```bash
./preview.py menu --demo --show                # fake data, no backend needed
./preview.py menu --demo --rotate 90 --show    # preview portrait
./preview.py menu --show                       # live, against /etc/celtech/env
./preview.py menu --watch                      # re-render every few seconds
```

What you see in the PNG is pixel-for-pixel what the TV shows.

---

## Updating

```bash
./update.sh menu
```

Fetches `main`, resets to it, restarts the service. **No npm, no build, no swap.**

---

## Gotchas

**Seeing "Hello from the pygame community"?** You're running old code. The framebuffer version imports no pygame. Check `grep -c pygame main.py` (must be `0`) and that `common/framebuffer.py` exists while `common/display.py` does not.

**Zero 2 W is 2.4GHz-only.** No 5GHz radio. If the SSID isn't broadcasting 2.4GHz, the unit silently never appears on the network.

**Reimaged?** `ssh-keygen -R druid-menu.local` — new host keys.

**Provision on bench WiFi**, not the truck's cellular router. The old Vue stack burned ~5GB of SIM data on `npm ci`. This one downloads ~20MB once, then a few KB per poll.

---

## Backend contract

`GET /api/menu/all` → `MenuItemView[]`, header `X-API-Key`.

```ts
MenuItemView {
  id: string
  name: string
  description: string | null
  priceCents: number            // integer cents on the wire
  priceDisplay: string | null   // server-formatted; often null
  categoryId: string
  categoryName: string
  badgeLabel: string | null
  badgeColor: 'gold' | 'grass' | 'sea' | null
  available: boolean            // false = 86'd
  sortOrder: number
  optionGroups: OptionGroup[]   // each with choices[] { label, priceDeltaCents, available }
}
```

The board groups the flat array into sections by `categoryId` and orders everything by `sortOrder`.
