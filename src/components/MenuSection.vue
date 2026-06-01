<script setup lang="ts">
import {computed} from 'vue';
import type {MenuSection, MenuItemView} from '../types/menu';
import {displayPrice, choiceDelta} from '../lib/format';

const props = defineProps<{section: MenuSection}>();

// Use the backend's display name as-is; it's already human-formatted.
const heading = computed(() => props.section.categoryName);

/**
 * Full option list per item, grouped by option group. Every available choice
 * is listed; the price delta is appended only when nonzero (e.g.
 * "Beer cheese +$1", "No meat -$1"). 86'd choices and groups are omitted so
 * the board only advertises what's actually orderable.
 */
interface OptionLine {
  groupLabel: string;
  choices: {label: string; delta: string}[];
}

function optionLines(item: MenuItemView): OptionLine[] {
  const out: OptionLine[] = [];
  for (const g of item.optionGroups) {
    if (!g.available) continue;
    const choices = g.choices
      .filter((c) => c.available)
      .map((c) => ({label: c.label, delta: choiceDelta(c)}));
    if (choices.length) out.push({groupLabel: g.label, choices});
  }
  return out;
}
</script>

<template>
  <section class="sec">
    <h2 class="sec__title">{{ heading }}</h2>
    <ul class="sec__list">
      <li v-for="it in section.items" :key="it.id" class="item">
        <div class="item__row">
          <span class="item__name">
            {{ it.name }}
            <span
              v-if="it.badgeLabel"
              class="badge"
              :data-color="it.badgeColor || 'default'"
              >{{ it.badgeLabel }}</span
            >
          </span>
          <span class="item__dots" aria-hidden="true" />
          <span class="item__price">{{ displayPrice(it) }}</span>
        </div>
        <p v-if="it.description" class="item__desc">{{ it.description }}</p>
        <div v-if="optionLines(it).length" class="item__opts">
          <p v-for="line in optionLines(it)" :key="line.groupLabel" class="optline">
            <span class="optline__group">{{ line.groupLabel }}:</span>
            <span
              v-for="(c, i) in line.choices"
              :key="c.label"
              class="optline__choice"
            >
              {{ c.label
              }}<span v-if="c.delta" class="optline__delta"> {{ c.delta }}</span
              ><span v-if="i < line.choices.length - 1">, </span>
            </span>
          </p>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.sec {
  break-inside: avoid;
  margin-bottom: 2.4rem;
}
.sec__title {
  font-family: var(--font-display);
  font-size: 2.3rem;
  font-weight: 500;
  color: var(--accent);
  margin: 0 0 1rem;
  padding-bottom: 0.35rem;
  border-bottom: 2px solid rgba(214, 178, 122, 0.35);
  letter-spacing: 0.01em;
}
.sec__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}
.item__row {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
}
.item__name {
  font-family: var(--font-body);
  font-size: 1.7rem;
  font-weight: 600;
  color: var(--ink);
}
.badge {
  display: inline-block;
  font-family: var(--font-body);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  margin-left: 0.5rem;
  vertical-align: middle;
  border: 1px solid currentColor;
}
.badge[data-color='gold'] {
  color: #e0b64a;
}
.badge[data-color='grass'] {
  color: #7bbf6a;
}
.badge[data-color='sea'] {
  color: #5fb3c4;
}
.badge[data-color='default'] {
  color: var(--ink-dim);
}
.item__dots {
  flex: 1;
  border-bottom: 2px dotted rgba(244, 238, 224, 0.25);
  transform: translateY(-0.35rem);
}
.item__price {
  font-family: var(--font-display);
  font-size: 1.7rem;
  color: var(--accent);
  white-space: nowrap;
}
.item__desc {
  font-family: var(--font-body);
  font-size: 1.1rem;
  font-weight: 300;
  line-height: 1.35;
  color: var(--ink-dim);
  margin: 0.25rem 0 0;
  max-width: 90%;
}
.item__opts {
  margin: 0.5rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.optline {
  margin: 0;
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 300;
  line-height: 1.4;
  color: var(--ink-dim);
  max-width: 92%;
}
.optline__group {
  font-weight: 600;
  color: var(--accent);
  margin-right: 0.35rem;
}
.optline__delta {
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
}
</style>