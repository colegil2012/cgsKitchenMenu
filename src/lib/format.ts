import type {MenuItemView, MenuChoice} from '../types/menu';

/** Format integer cents as a dollar string, e.g. 550 -> "$5.50", 300 -> "$3". */
export function centsToDollars(cents: number): string {
  if (typeof cents !== 'number' || Number.isNaN(cents)) return '—';
  const dollars = cents / 100;
  return Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`;
}

/**
 * Display price for an item. Prefer the server-formatted `priceDisplay` when
 * present; otherwise format from `priceCents`. Never throws on missing data.
 */
export function displayPrice(item: MenuItemView): string {
  if (item.priceDisplay) return item.priceDisplay;
  return centsToDollars(item.priceCents);
}

/**
 * A short "+$X" suffix for an option choice that costs extra, or "" for no
 * delta. Negative deltas (e.g. "No meat -$1") are shown with a minus.
 */
export function choiceDelta(choice: MenuChoice): string {
  const d = choice.priceDeltaCents;
  if (!d) return '';
  const abs = centsToDollars(Math.abs(d));
  return d > 0 ? `+${abs}` : `-${abs}`;
}