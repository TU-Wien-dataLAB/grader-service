import React from 'react';
import {
  columnFilteringFeature,
  createExpandedRowModel,
  createFilteredRowModel,
  FilterFn,
  filterFn_equalsString,
  filterFn_includesString,
  globalFilteringFeature,
  Row,
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
import { ChevronDown, ChevronRight, CornerDownRight } from 'lucide-react';
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
import { NoResultsFoundIcon } from '../../../../assets/no-results-found-icon';
import { EmptyState } from '../../utils/empty-state';

// custom function that checks if a cell value is included in the filters' list
const filterFn_valueInList: FilterFn<any, any> = (
  row,
  columnId,
  filterValue: string[]
) => {
  const v = row.getValue<string>(columnId);
  return filterValue.includes(v);
};
filterFn_valueInList.autoRemove = (val: string[]) => !val?.length;

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
    filterFn_equalsString,
    filterFn_valueInList
  }
});

export type DataTableColumnDef<T> = ColumnDef<typeof dataTableFeatures, T>;

export const INDENT_STEP = 32;
function ExpandButton<T>({ row }: { row: Row<typeof dataTableFeatures, T> }) {
  return (
    <div className="relative size-4">
      <Button
        variant="ghost"
        size="icon"
        className={`absolute -top-2 -left-2 size-8`}
        onClick={row.getToggleExpandedHandler()}
        aria-label={row.getIsExpanded() ? 'Collapse row' : 'Expand row'}
      >
        {row.getIsExpanded() ? (
          <ChevronDown className={'text-primary'} />
        ) : (
          <ChevronRight className={'text-primary'} />
        )}
      </Button>
    </div>
  );
}

function RowCheckbox<T>({ row }: { row: Row<typeof dataTableFeatures, T> }) {
  return (
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
  );
}

// only for top rows
export function expanderColumn<T>(): DataTableColumnDef<T> {
  return {
    id: 'expander',
    header: () => null,
    enableGlobalFilter: false,
    cell: ({ row }) =>
      row.depth === 0 && row.getCanExpand() ? <ExpandButton row={row} /> : null
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
    cell: ({ row }) =>
      row.depth === 0 ? (
        <RowCheckbox row={row} />
      ) : (
        // expandable successors have expand button instead of the icon
        <div className="relative size-4">
          {row.getCanExpand() ? (
            <div
              className="absolute top-0"
              style={{ left: (row.depth - 1) * INDENT_STEP }}
            >
              <ExpandButton row={row} />
            </div>
          ) : (
            <CornerDownRight
              className="absolute top-0 size-4 text-border"
              style={{ left: (row.depth - 1) * INDENT_STEP }}
            />
          )}
          <div
            className="absolute top-0"
            style={{ left: row.depth * INDENT_STEP }}
          >
            <RowCheckbox row={row} />
          </div>
        </div>
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
  rowSelection?: RowSelectionState /** keyed by row id. */;
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
    autoResetExpanded: false,

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
              className="data-[state=selected]:bg-[#E0E7EB]"
            >
              {row.getAllCells().map(cell => (
                <TableCell key={cell.id}>
                  <table.FlexRender cell={cell} />
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : (
          <EmptyState
            icon={<NoResultsFoundIcon />}
            title={'No results found'}
            description={
              'Try adjusting your search or ' +
              "filter to find what \n you're looking for."
            }
          />
        )}
      </TableBody>
    </Table>
  );
}
