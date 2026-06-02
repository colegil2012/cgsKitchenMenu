# CGS Kitchen Menu Board — Vue display for cgsKitchen

Standalone customer-facing menu board for the food truck, built as a static web
app that runs in the **same Chromium-kiosk-on-a-Pi** pattern as the driver unit
and the POS. It is a **read-only** display: a screen facing customers showing
the full menu, grouped by category, with each item's options listed and 86'd
items and choices shown struck through. It does not take orders or write
anything back. Built for a **Pi Zero 2 W** driving a TV or large screen.

## Why this architecture

The driver kiosk and the POS already run Chromium fullscreen on labwc, loading
a local web app. This board reuses that exact stack — another Pi provisioned
the same way, only the launched URL differs. No new device class, one
provisioning playbook. The board is **standalone**: it only consumes cgsKitchen
endpoints and writes nothing back. New data needs become new endpoints in
cgsKitchen, not coupling into this app.

It reads cgsKitchen's **full** menu endpoint (`GET /api/menu/all`) on the
API-key filter chain, the same chain the POS uses (the old keyless
`/api/public/menu` was removed when the menu read was consolidated behind the
key, so this board carries the key like every other device). It deliberately
uses `/api/menu/all` rather than the POS's orderable `/api/menu/menu`: the
latter is backed by `findAvailable` and pre-filters 86'd entries, so it could
never drive the sold-out styling. `/api/menu/all` returns everything —
including 86'd items and choices — and the board renders the unavailable ones
struck through. One menu, one source of truth: 86 an item on the POS and it
shows as sold out here on the next poll, with no second feed to keep in sync.

## Authentication

Every request sends the `X-API-Key` header (set from `VITE_API_KEY`, which must
match the backend `app.api-key`). The menu read lives on the backend's API-key
filter chain (`/api/**`), same as the POS — there is no public, keyless
endpoint. Vite inlines `VITE_*` vars at build time, so changing `.env` requires
a rebuild, not just a refresh.

## What it talks to

All endpoints are on the cgsKitchen backend.

| Action | Endpoint | On drop |
|---|---|---|
| Load full menu (incl. 86'd) | `GET /api/menu/all` | last-known menu stays up; polls when online |

This is cgsKitchen's full-menu read on the same API-key chain the POS uses, so
the customer board and the cashier draw from one source. No new server
endpoints are required.

## Features

### The board
Items from `GET /api/menu/all` are grouped by category into a two-column
editorial layout — serif display headings, dotted price leaders between item
and price, an optional description line per item, and the item's full option
list beneath. Categories and items are ordered by the backend's `sortOrder`,
so the truck controls layout from cgsKitchen rather than per-Pi config. Polled
every 30s; menus change far less often than orders (mostly via 86'ing), so a
slow poll keeps the screen current without hammering the backend.

### Option lists
Each item shows its option groups (Protein, Cheese, Veggies, Sauces, …) with
every choice listed. A price delta is appended only when nonzero — e.g.
`Cheese: Cheddar, Swiss, Beer cheese +$1, No cheese`. Free choices show plain;
discounts show a minus (`No meat -$1`). This advertises the build-your-own
options without duplicating the POS's full picker.

### 86-aware (the point)
The board shows the **full** menu and marks what's out rather than hiding it.
An item with `available: false` stays in place, dimmed, with its name and price
struck through and a small red "Sold out" tag (its badge and options are hidden
while out). An individual 86'd **choice** — say Beer cheese sells out — stays in
its option line struck through, so customers still see it exists but know it's
unavailable. Un-86 on the POS and it returns to normal on the next poll. This
is the whole reason the board reads `/api/menu/all` instead of the filtered
orderable endpoint.

### Badges
In-stock items carry their backend badge (`Most Loved`, `Top Seller`, `New`)
in the matching accent color (gold / grass / sea). Badges are hidden on
sold-out items.

### Connectivity behaviour
On a drop the board keeps the last good menu on screen rather than blanking the
display, shows a small stale indicator, and silently resumes when the next poll
succeeds.

## Why read-only

The customer board is pure output: it shows what's for sale. It holds no cart,
no order state, and no write path — ordering happens at the POS. Keeping it
read-only means it can never get into a bad state worth recovering, and a menu
drop degrades to "show the last menu we saw" rather than an error screen in
front of a customer.

## Project layout

```
src/
  api/client.ts            fetch wrapper (X-API-Key) + fetchMenu (/api/menu/all)
  lib/config.ts            Vite env config (base url, key, poll, title)
  lib/format.ts            centsToDollars, displayPrice, choiceDelta
  types/menu.ts            MenuItemView/OptionGroup/MenuChoice + MenuSection
  components/MenuSection.vue   category heading + item rows, options, sold-out
  App.vue                  polls menu, groups by category, orders by sortOrder
  main.ts                  entry
  styles.css               theme tokens + global kiosk styles (cursor: none)
```

There is no `stores/` folder — the board's single poll lives directly in
`App.vue`, so Pinia isn't pulled in. (The kitchen board uses a store because it
has more moving state; the menu board doesn't need one.)

## Develop

```bash
npm install
cp .env.example .env       # set VITE_API_BASE_URL, VITE_API_KEY
npm run dev                # http://localhost:5174
```

`VITE_API_KEY` must match the backend `app.api-key`. For local backend dev,
set `API_KEY` and add `http://localhost:5174` to `CORS_ORIGINS` in the
cgsKitchen run config. `npm run build` typechecks (vue-tsc) then emits `dist/`.

### Environment variables

- `VITE_API_BASE_URL` — backend base, e.g. `http://192.168.1.50:8080`
- `VITE_API_KEY` — must match backend `app.api-key`
- `VITE_POLL_MS` — menu refresh interval (default 30000)
- `VITE_BOARD_TITLE` — heading text (default `Menu`)

Category and item order is **not** configured here — it follows the backend's
`sortOrder`, so reordering the menu is done in cgsKitchen and reflected on the
board on the next poll.

## Deploy to the Pi kiosk

The build output is plain static files with **relative** asset paths
(`base: './'`), so it loads via `file://` exactly like the driver dashboard
and the POS. Two options:

**A. Mirror the driver unit (recommended).** Provision a Pi Zero 2 W with the
same buildout doc (labwc + systemd autologin + `update.sh` git pull). Build and
commit `dist/`, or have `update.sh` run `npm ci && npm run build` after the
pull. Point `launch.sh` at the built file:

```bash
exec chromium \
  --kiosk --noerrdialogs --disable-infobars --no-first-run \
  --ozone-platform=wayland --password-store=basic \
  --enable-features=UseOzonePlatform \
  --app=file:///home/druid-mobile/celtech-menu-board/dist/index.html
```

**B. Serve from the network** and point `--app=` at the URL instead. Simpler
rebuilds, but then the kiosk needs connectivity to load the shell.

Notes for the Zero 2 W: the app ships tiny (~26 KB gzipped JS, no images) and
polls slowly, so it idles comfortably. `cursor: none` is set so no pointer
shows on the customer-facing TV. There is no input — this is display-only.

## Offline-readiness checklist (do before relying on it cold)

1. **Self-host fonts.** `styles.css` pulls Fraunces and Nunito Sans from Google
   Fonts, which needs network on first paint. Vendor the woff2 files and swap
   for a local `@font-face`. System-ui/Georgia fallbacks already prevent a hard
   fail, but the board's character depends on the display serif.
2. **API reachable on the LAN IP.** Keep `VITE_API_BASE_URL` pointed at the
   backend's LAN IP if serving the shell over the network. Option A (file://)
   makes the shell itself network-independent; only the menu poll needs the LAN.

## Production hardening notes

- The API key ships in the built bundle. Fine for one trusted kiosk on a
  private network; revisit (per-device key / backend proxy) before any broader
  rollout. Same posture as the POS.
- Read-only by construction, so there is no last-write-wins concern — the board
  makes no changes and can't clobber anything.

## Roadmap

- **Push instead of poll.** If cgsKitchen grows an SSE/WebSocket menu/inventory
  stream, swap the 30s poll for a subscription so an 86 reflects instantly.
- **Prices/specials styling.** Featured-item callouts, daily-special ribbon,
  per-category imagery if the menu DTO grows image URLs.
- **Multi-screen layout.** A wide or portrait variant for different screen
  orientations; the two-column layout already collapses to one column on
  narrow viewports.
- **Self-hosted fonts** for full cold-start independence (see checklist).
- **Branding.** Logo in the header, favicon.