/**
 * Mirrors the cgsKitchen MenuItemView returned by GET /api/menu/menu.
 *
 * Money is integer cents on the wire (`priceCents`, `priceDeltaCents`).
 * `priceDisplay` is a server-formatted string but is often null, so the
 * board formats from cents itself (see lib/format) and only uses
 * priceDisplay when present.
 */
export interface MenuChoice {
  id: string;
  label: string;
  priceDeltaCents: number;
  available: boolean;
  unavailableReason: string | null;
  defaultChoice: boolean;
}

export type SelectionType = 'SINGLE' | 'MULTI';

export interface OptionGroup {
  id: string;
  label: string;
  selectionType: SelectionType;
  required: boolean;
  available: boolean;
  unavailableReason: string | null;
  maxSelections: number;
  choices: MenuChoice[];
}

export interface MenuItemView {
  id: string;
  name: string;
  description: string | null;
  priceCents: number;
  priceDisplay: string | null;
  categoryId: string;
  categoryName: string;
  badgeId: string | null;
  badgeLabel: string | null;
  badgeColor: string | null;
  available: boolean;
  sortOrder: number;
  optionGroups: OptionGroup[];
}

/** A category with its in-stock items, ready to render as a board section. */
export interface MenuSection {
  categoryId: string;
  categoryName: string;
  sortOrder: number;
  items: MenuItemView[];
}