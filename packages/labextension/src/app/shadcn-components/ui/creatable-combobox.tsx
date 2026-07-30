'use client';

import * as React from 'react';
import {
  Combobox as ComboboxPrimitive,
  ComboboxRootChangeEventDetails
} from '@base-ui/react';

import { cn } from '../../lib/utils';
import { Combobox } from './combobox';
import { Plus } from 'lucide-react';

// ─── Creatable ────────────────────────────────────────────────────────

type CreatableItem = {
  creatable: true; // literal true, not boolean
  label: string;
  value: string;
};

const isCreatableItem = (item: unknown): item is CreatableItem => {
  return (
    typeof item === 'object' &&
    item !== null &&
    (item as CreatableItem).creatable === true
  );
};
// ─── Internal helpers ─────────────────────────────────────────────────────────

/** Display string for an item — mirrors base-ui's own default logic. */
const toLabel = (item: unknown): string => {
  if (typeof item === 'string') {
    return item;
  }
  if (item && typeof item === 'object') {
    if ('label' in item) {
      return String((item as { label: unknown }).label);
    }
    if ('value' in item) {
      return String((item as { value: unknown }).value);
    }
  }
  return String(item);
};

/** Equality key for an item — prefers .value for stable identity. */
const toValueKey = (item: unknown): string => {
  if (typeof item === 'string') {
    return item;
  }
  if (item && typeof item === 'object') {
    if ('value' in item) {
      return String((item as { value: unknown }).value);
    }
    if ('label' in item) {
      return String((item as { label: unknown }).label);
    }
  }
  return String(item);
};

// ─── CreatableCombobox ────────────────────────────────────────────────────────

type ComboboxRootProps = React.ComponentProps<typeof ComboboxPrimitive.Root>;

type CreatableComboboxProps = ComboboxRootProps & {
  /**
   * Called when the user confirms a new value that doesn't exist in the list.
   * Receives the raw typed string value.
   */
  /**
   * onValueChange will never be called with a CreatableItem.
   * Use onCreateValue to handle new value creation.
   */
  onCreateValue: (value: string) => void;

  /** Label for the "Create" option. Defaults to `Create "${value}"`. */
  createLabel?: (value: string) => string;

  /** Where the create option appears in the list. Defaults to "first". */
  createOptionPosition?: 'first' | 'last';
};

/**
 * A combobox that allows the user to create new values.
 *
 * @description
 * Follows the base-ui creatable combobox example pattern:
 * https://base-ui.com/react/components/combobox#creatable
 *
 * Instead of a boolean flag, `creatable` holds the raw typed string.
 * This means isCreatableItem doubles as a type guard AND gives you the original
 * query back without any extra state — `item.creatable` is the value to create.
 *
 * @param props - The props for the creatable combobox.
 * @param props.items - The items of the creatable combobox.
 * @param props.onCreateValue - The function to call when the user creates a new value.
 * @param props.createLabel - The label for the create option.
 * @param props.createOptionPosition - The position of the create option in the list.
 * @see https://base-ui.com/react/components/combobox
 * @returns The creatable combobox.
 */
function CreatableCombobox({
  children,
  items = [],
  onCreateValue,
  createLabel = v => `Create "${v}"`,
  createOptionPosition = 'first',
  ...props
}: CreatableComboboxProps) {
  const initialLabel = React.useMemo(() => {
    if (props.value === undefined || props.value === null) return '';
    return props.itemToStringLabel?.(props.value) ?? toLabel(props.value);
  }, []); // intentionally only on mount

  const [query, setQuery] = React.useState<string>(initialLabel);
  const pendingCreateRef = React.useRef<string | null>(null);

  // Augment items with the creatable item if there's no exact match
  const augmentedItems = (() => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      return items;
    }

    const lowered = trimmedQuery.toLocaleLowerCase();
    const exactMatch = items.some(
      item => toLabel(item).toLocaleLowerCase() === lowered
    );

    if (exactMatch) {
      return items;
    }

    // Show the creatable item alongside matches
    const createItem: CreatableItem = {
      creatable: true,
      label: createLabel(trimmedQuery),
      value: trimmedQuery
    };

    return createOptionPosition === 'first'
      ? [createItem, ...items]
      : [...items, createItem];
  })();

  const handleValueChange = (
    next: unknown,
    details: ComboboxRootChangeEventDetails
  ) => {
    // multiple select
    if (props.multiple && Array.isArray(next)) {
      const creatable = next.find(isCreatableItem);
      const clean = next.filter(item => !isCreatableItem(item));

      if (creatable) {
        pendingCreateRef.current = creatable.value;
        setQuery('');
      }

      props.onValueChange?.(clean, details);
      return;
    }

    // single select
    if (isCreatableItem(next)) {
      pendingCreateRef.current = next.value;
      setQuery('');
      props.onValueChange?.(next.value, details);
      return;
    }

    // pass through overrides or use base-ui default onValueChange behavior
    props.onValueChange?.(next, details);
  };

  return (
    <Combobox
      {...props}
      items={augmentedItems}
      inputValue={query}
      onInputValueChange={setQuery}
      onValueChange={handleValueChange}
      onOpenChangeComplete={open => {
        if (!open && pendingCreateRef.current) {
          onCreateValue(pendingCreateRef.current);
          pendingCreateRef.current = null;
        }
        props.onOpenChangeComplete?.(open);
      }}
      itemToStringLabel={(item: unknown): string => {
        if (isCreatableItem(item)) {
          return item.value;
        }
        // pass through overrides or uses base-ui default itemToStringLabel
        return props.itemToStringLabel?.(item) ?? toLabel(item);
      }}
      isItemEqualToValue={(a: unknown, b: unknown) => {
        if (isCreatableItem(a) || isCreatableItem(b)) {
          return toValueKey(a) === toValueKey(b);
        }
        // pass through overrides or uses base-ui default Object.is
        return props.isItemEqualToValue?.(a, b) ?? Object.is(a, b);
      }}
    >
      {children}
    </Combobox>
  );
}

function ComboboxItemCreatable({
  className,
  children,
  value,
  showPlus = true,
  ...props
}: Omit<ComboboxPrimitive.Item.Props, 'value'> & {
  value: CreatableItem;
  showPlus?: boolean;
}) {
  return (
    <ComboboxPrimitive.Item
      data-creatable
      data-slot="combobox-item"
      value={value}
      className={cn(
        "relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-hidden select-none data-highlighted:bg-accent data-highlighted:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    >
      {showPlus && <Plus className="size-3.5 shrink-0 opacity-60" />}
      {children ?? value.label}
    </ComboboxPrimitive.Item>
  );
}

export {
  CreatableCombobox,
  type CreatableComboboxProps,
  ComboboxItemCreatable,
  type CreatableItem,
  isCreatableItem
};
