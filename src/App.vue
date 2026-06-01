<script setup lang="ts">
import {ref, computed, onMounted, onUnmounted} from 'vue';
import {fetchMenu} from './api/client';
import {POLL_MS, BOARD_TITLE} from './lib/config';
import type {MenuItemView, MenuSection} from './types/menu';
import MenuSectionView from './components/MenuSection.vue';

const items = ref<MenuItemView[]>([]);
const online = ref(true);
const loaded = ref(false);

let timer: ReturnType<typeof setInterval> | null = null;
let inFlight: AbortController | null = null;

/**
 * Group available items by category and order everything by the backend's
 * sortOrder so the truck controls layout from cgsKitchen, not per-Pi config.
 * Only in-stock items are shown to customers; 86'd items vanish entirely.
 * A category whose items are all 86'd drops off the board too.
 */
const sections = computed<MenuSection[]>(() => {
  const groups = new Map<string, MenuSection>();
  for (const it of items.value) {
    if (!it.available) continue;
    let sec = groups.get(it.categoryId);
    if (!sec) {
      sec = {
        categoryId: it.categoryId,
        categoryName: it.categoryName,
        // Category position = its smallest item sortOrder.
        sortOrder: it.sortOrder,
        items: [],
      };
      groups.set(it.categoryId, sec);
    }
    sec.items.push(it);
    if (it.sortOrder < sec.sortOrder) sec.sortOrder = it.sortOrder;
  }

  const out = [...groups.values()];
  out.sort((a, b) => a.sortOrder - b.sortOrder);
  for (const sec of out) {
    sec.items.sort((a, b) => a.sortOrder - b.sortOrder);
  }
  return out;
});

async function refresh() {
  inFlight?.abort();
  inFlight = new AbortController();
  try {
    items.value = await fetchMenu(inFlight.signal);
    online.value = true;
    loaded.value = true;
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') return;
    online.value = false;
    // Keep the last good menu on screen rather than blanking the display.
  }
}

onMounted(() => {
  refresh();
  timer = setInterval(refresh, POLL_MS);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
  inFlight?.abort();
});
</script>

<template>
  <div class="menu">
    <header class="menu__head">
      <h1 class="menu__brand">CGS</h1>
      <p class="menu__title">{{ BOARD_TITLE }}</p>
      <span
        v-if="!online && loaded"
        class="menu__stale"
        title="Showing last known menu"
        >●</span
      >
    </header>

    <main class="menu__cols">
      <MenuSectionView
        v-for="sec in sections"
        :key="sec.categoryId"
        :section="sec"
      />
      <p v-if="loaded && sections.length === 0" class="menu__empty">
        Today's menu is being prepared.
      </p>
    </main>
  </div>
</template>

<style scoped>
.menu {
  min-height: 100vh;
  padding: 2.4rem 3rem 3rem;
  background:
    radial-gradient(
      130% 90% at 80% 0%,
      rgba(214, 178, 122, 0.07),
      transparent 55%
    ),
    var(--bg);
}
.menu__head {
  display: flex;
  align-items: baseline;
  gap: 1.2rem;
  margin-bottom: 2.2rem;
  padding-bottom: 1rem;
  border-bottom: 3px double rgba(214, 178, 122, 0.4);
}
.menu__brand {
  font-family: var(--font-display);
  font-size: 3.2rem;
  font-weight: 600;
  color: var(--ink);
  margin: 0;
  letter-spacing: 0.04em;
}
.menu__title {
  font-family: var(--font-body);
  font-size: 1.3rem;
  font-weight: 300;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0;
}
.menu__stale {
  margin-left: auto;
  color: #c0563f;
  font-size: 0.9rem;
  align-self: center;
  opacity: 0.7;
}
.menu__cols {
  column-count: 2;
  column-gap: 4rem;
}
@media (max-width: 900px) {
  .menu__cols {
    column-count: 1;
  }
}
.menu__empty {
  font-family: var(--font-display);
  font-size: 1.8rem;
  color: var(--ink-dim);
  text-align: center;
  margin-top: 4rem;
}
</style>