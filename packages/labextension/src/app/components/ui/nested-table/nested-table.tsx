import {
  columnFilteringFeature,
  createExpandedRowModel,
  createFilteredRowModel,
  filterFns,
  globalFilteringFeature,
  rowExpandingFeature,
  rowSelectionFeature,
  tableFeatures,
  useTable
} from '@tanstack/react-table';
import type {
  ColumnDef,
  ColumnFiltersState,
  OnChangeFn,
  RowSelectionState
} from '@tanstack/react-table';
import { ChevronDown, ChevronRight } from 'lucide-react';

import React from 'react';
import { Button } from '../../../shadcn-components/ui/button';
import { Checkbox } from '../../../shadcn-components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '../../../shadcn-components/ui/table';

// Features are defined once and exported so column defs can be typed against them.
export const dataTableFeatures = tableFeatures({
  columnFilteringFeature,
  globalFilteringFeature, // requires columnFilteringFeature
  rowExpandingFeature,
  rowSelectionFeature,
  filteredRowModel: createFilteredRowModel(), // client-side filtering
  expandedRowModel: createExpandedRowModel(), // client-side expanding
  filterFns // all built-in filter fns (includesString, equalsString, ...)
});

export type DataTableColumnDef<TData> = ColumnDef<
  typeof dataTableFeatures,
  TData
>;

export function expanderColumn<TData>(): DataTableColumnDef<TData> {
  return {
    id: 'expander',
    header: () => null,
    enableGlobalFilter: false,
    cell: ({ row }) =>
      row.getCanExpand() ? (
        <Button
          variant="ghost"
          size="icon"
          className="size-6"
          onClick={row.getToggleExpandedHandler()}
          aria-label={row.getIsExpanded() ? 'Collapse row' : 'Expand row'}
        >
          {row.getIsExpanded() ? (
            <ChevronDown className="size-4" />
          ) : (
            <ChevronRight className="size-4" />
          )}
        </Button>
      ) : null
  };
}

export function selectColumn<TData>(): DataTableColumnDef<TData> {
  return {
    id: 'select',
    enableGlobalFilter: false,
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllRowsSelected()
            ? true
            : table.getIsSomeRowsSelected()
              ? 'indeterminate'
              : false
        }
        onCheckedChange={value => table.toggleAllRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={
          row.getIsSelected() ||
          (row.getCanSelectSubRows() && row.getIsAllSubRowsSelected())
            ? true
            : row.getIsSomeSelected()
              ? 'indeterminate'
              : false
        }
        onCheckedChange={value => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    )
  };
}

type DataTableProps<TData> = {
  columns: Array<DataTableColumnDef<TData>>;
  data: Array<TData>;

  /** Where a row's children live. Omit for a flat table. */
  getSubRows?: (row: TData) => Array<TData> | undefined;
  /** Stable ids so selection/expanded state survives data changes. */
  getRowId?: (row: TData) => string;

  /** Search text. Provide both props to control it from the parent. */
  globalFilter?: string;
  onGlobalFilterChange?: (value: string) => void;

  /** Per-column filters, e.g. [{ id: 'grading', value: 'failed' }] */
  columnFilters?: ColumnFiltersState;
  onColumnFiltersChange?: OnChangeFn<ColumnFiltersState>;

  /** Selected rows, keyed by row id. */
  rowSelection?: RowSelectionState;
  onRowSelectionChange?: OnChangeFn<RowSelectionState>;

  emptyMessage?: string;
};

export function DataTable<TData>({
  columns,
  data,
  getSubRows,
  getRowId,
  globalFilter,
  onGlobalFilterChange,
  columnFilters,
  onColumnFiltersChange,
  rowSelection,
  onRowSelectionChange,
  emptyMessage = 'No results.'
}: DataTableProps<TData>) {
  const table = useTable({
    features: dataTableFeatures,
    columns,
    data,
    getSubRows,
    getRowId,

    globalFilterFn: 'includesString',
    // Keep a parent visible when one of its children matches.
    filterFromLeafRows: true,

    // Only hand a slice to the table when the parent actually controls it.
    // Anything left out stays managed internally by the table.
    state: {
      ...(globalFilter !== undefined && { globalFilter }),
      ...(columnFilters !== undefined && { columnFilters }),
      ...(rowSelection !== undefined && { rowSelection })
    },

    // The table gives us an updater (value or function); the parent gets a plain string.
    onGlobalFilterChange: onGlobalFilterChange
      ? updater =>
          onGlobalFilterChange(
            typeof updater === 'function'
              ? updater(globalFilter ?? '')
              : updater
          )
      : undefined,
    onColumnFiltersChange,
    onRowSelectionChange
  });

  const rows = table.getRowModel().rows;

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map(headerGroup => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map(header => (
              <TableHead key={header.id}>
                {header.isPlaceholder ? null : (
                  <table.FlexRender header={header} />
                )}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {rows.length ? (
          rows.map(row => (
            <TableRow
              key={row.id}
              data-state={row.getIsSelected() && 'selected'}
            >
              {row.getAllCells().map(cell => (
                <TableCell key={cell.id}>
                  <table.FlexRender cell={cell} />
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell
              colSpan={columns.length}
              className="h-24 text-center text-muted-foreground"
            >
              {emptyMessage}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
