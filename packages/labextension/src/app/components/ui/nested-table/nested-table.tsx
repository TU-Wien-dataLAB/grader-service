import React from 'react';
import {
  columnFilteringFeature,
  createExpandedRowModel,
  createFilteredRowModel,
  filterFn_equalsString,
  filterFn_includesString,
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

export const dataTableFeatures = tableFeatures({
  columnFilteringFeature,
  globalFilteringFeature,
  rowExpandingFeature,
  rowSelectionFeature,
  filteredRowModel: createFilteredRowModel(),
  expandedRowModel: createExpandedRowModel(),

  // As filterFns is deprecated in new tanstack/react-table version, to add new function look up https://github.com/TanStack/table/blob/main/packages/table-core/src/features/column-filtering/filterFns.ts#L442
  filterFns: {
    filterFn_includesString,
    filterFn_equalsString
  }
});

export type DataTableColumnDef<T> = ColumnDef<typeof dataTableFeatures, T>;

export function expanderColumn<T>(): DataTableColumnDef<T> {
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

export function selectColumn<T>(): DataTableColumnDef<T> {
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

type DataTableProps<T> = {
  columns: Array<DataTableColumnDef<T>>;
  data: Array<T>;
  getSubRows?: (row: T) => Array<T> | undefined;
  getRowId?: (row: T) => string;
  globalFilter?: string;
  onGlobalFilterChange?: (value: string) => void;
  columnFilters?: ColumnFiltersState;
  onColumnFiltersChange?: OnChangeFn<ColumnFiltersState>;
  rowSelection?: RowSelectionState; /** keyed by row id. */
  onRowSelectionChange?: OnChangeFn<RowSelectionState>;
  emptyMessage?: string;
};

export function NestedTable<T>({
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
}: DataTableProps<T>) {
  const table = useTable({
    features: dataTableFeatures,
    columns,
    data,
    getSubRows,
    getRowId,

    globalFilterFn: 'filterFn_includesString',
    filterFromLeafRows: true,

    // Only hand a slice to the table when the parent actually controls it.
    // Anything left out stays managed internally by the table.
    state: {
      ...(globalFilter !== undefined && { globalFilter }),
      ...(columnFilters !== undefined && { columnFilters }),
      ...(rowSelection !== undefined && { rowSelection })
    },

    // The table gives us an updater (value or function), the parent gets a plain string
    onGlobalFilterChange: onGlobalFilterChange
      ? updater =>
          onGlobalFilterChange(
            typeof updater === 'function'
              ? updater(globalFilter ?? '')
              : updater
          )
      : undefined, // TODO: review filter's logic and ways
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
