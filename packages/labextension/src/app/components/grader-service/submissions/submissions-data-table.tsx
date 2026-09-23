import {
  CircleAlert,
  CircleCheck,
  Eye,
  History,
  TriangleAlert
} from 'lucide-react';

import React, { useMemo } from 'react';
import { Button } from '../../../shadcn-components/ui/button';
import {
  DataTable,
  DataTableColumnDef,
  expanderColumn,
  selectColumn
} from '../../ui/nested-table/nested-table';
import {
  ColumnFiltersState,
  OnChangeFn,
  RowSelectionState
} from '@tanstack/react-table';

type Grading = 'graded' | 'failed' | 'not_graded';

type SubmissionRow = {
  id: string;
  student: string; // present on parents AND children so search matches every row
  label?: string; // e.g. "Submission 2" (children only)
  score?: number;
  grading?: Grading;
  feedback?: boolean;
  subRows?: Array<SubmissionRow>;
};

const data: Array<SubmissionRow> = [
  {
    id: 'lina',
    student: 'Lina Hoffmann',
    subRows: [
      {
        id: 'lina-2',
        student: 'Lina Hoffmann',
        label: 'Submission 2',
        score: 283,
        grading: 'failed',
        feedback: false
      },
      {
        id: 'lina-1',
        student: 'Lina Hoffmann',
        label: 'Submission 1',
        score: 750,
        grading: 'graded',
        feedback: true
      }
    ]
  },
  {
    id: 'mateo',
    student: 'Mateo Alvarez',
    score: 0,
    grading: 'not_graded',
    feedback: false
  },
  {
    id: 'aisha',
    student: 'Aisha Rahman',
    score: 800,
    grading: 'graded',
    feedback: true
  }
];

const gradingLabel: Record<Grading, React.ReactNode> = {
  graded: (
    <span className="flex items-center gap-2">
      <CircleCheck className="size-4 text-green-600" /> Graded
    </span>
  ),
  failed: (
    <span className="flex items-center gap-2">
      <CircleAlert className="size-4 text-red-600" /> Grading failed
    </span>
  ),
  not_graded: (
    <span className="flex items-center gap-2">
      <TriangleAlert className="size-4 text-amber-500" /> Not graded
    </span>
  )
};

const columns: Array<DataTableColumnDef<SubmissionRow>> = [
  expanderColumn<SubmissionRow>(),
  selectColumn<SubmissionRow>(),
  {
    accessorKey: 'student',
    header: 'Name',
    cell: ({ row }) => (
      <span style={{ paddingLeft: row.depth * 24 }}>
        {row.original.label ?? row.original.student}
      </span>
    )
  },
  {
    accessorKey: 'score',
    header: 'Final score',
    enableGlobalFilter: false, // search box ignores this column
    cell: ({ getValue }) => {
      const score = getValue<number | undefined>();
      return score === undefined ? null : `${score.toFixed(2)} / 800`;
    }
  },
  {
    accessorKey: 'grading',
    header: 'Grading',
    enableGlobalFilter: false,
    filterFn: 'equalsString', // exact match, so "graded" doesn't match "not_graded"
    cell: ({ getValue }) => {
      const grading = getValue<Grading | undefined>();
      return grading ? gradingLabel[grading] : null;
    }
  },
  {
    accessorKey: 'feedback',
    header: 'Feedback',
    enableGlobalFilter: false,
    cell: ({ row, getValue }) => {
      if (row.original.grading === undefined) return null;
      return getValue<boolean>() ? (
        <span className="flex items-center gap-2">
          <CircleCheck className="size-4 text-green-600" /> Feedback given
        </span>
      ) : (
        <span className="flex items-center gap-2">
          <CircleAlert className="size-4 text-red-600" /> No feedback
        </span>
      );
    }
  },
  {
    id: 'actions',
    header: 'Actions',
    enableGlobalFilter: false,
    cell: ({ row }) =>
      row.original.grading === undefined ? null : (
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" title="View submission details">
            <Eye className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" title="View logs">
            <History className="size-4" />
          </Button>
        </div>
      )
  }
];

type TTableProps = {
  grading: string;
  search?: string;
  setSearch: (val: string) => void;
  columnFilters: Set<string>;
  rowSelection: RowSelectionState;
  onRowSelectionChange: OnChangeFn<RowSelectionState>;
};

const SubmissionsDataTable = (props: TTableProps) => {
  const { grading, search, rowSelection, onRowSelectionChange, setSearch } =
    props;

  const columnFilters = useMemo<ColumnFiltersState>(
    () => (grading === 'all' ? [] : [{ id: 'grading', value: grading }]),
    [grading]
  );

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        data={data}
        getSubRows={row => row.subRows}
        getRowId={row => row.id}
        globalFilter={search}
        onGlobalFilterChange={setSearch}
        columnFilters={columnFilters}
        rowSelection={rowSelection}
        onRowSelectionChange={onRowSelectionChange}
        emptyMessage="No submissions match your filters."
      />
    </div>
  );
};

export default SubmissionsDataTable;
