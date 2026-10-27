import React, { useMemo, useState } from 'react';
import {
  CircleAlert,
  CircleCheck,
  Eye,
  History,
  OctagonAlert,
  TriangleAlert
} from 'lucide-react';
import type {
  ColumnFiltersState,
  OnChangeFn,
  RowSelectionState
} from '@tanstack/react-table';
import { Button } from '../../../shadcn-components/ui/button';
import {
  NestedTable,
  expanderColumn,
  selectColumn,
  RowCheckbox
} from '../../ui/nested-table/nested-table';
import type { DataTableColumnDef } from '../../ui/nested-table/nested-table';
import { Submission } from '../../../../model/submission';
import { SubmissionDetailsDialog } from './submission-details-dialog';
import { toSubmissionRows } from './utils';
import { FeedbackStatus } from '../../../../model/feedbackStatus';
import { AutoStatus } from '../../../../model/autoStatus';

/* row  */

export type SubmissionRow = {
  id: string;
  studentName: string;
  label?: string;
  score?: number;
  gradingStatus?: AutoStatus;
  feedbackStatus?: FeedbackStatus;
  submission?: Submission;
  subRows?: Array<SubmissionRow>;
};

const gradingLabel: Record<AutoStatus, React.ReactNode> = {
  pending: (
    <span className="flex items-center gap-2">
      <CircleCheck color="#6A9816" className="size-4" /> Pending
    </span>
  ),
  grading_failed: (
    <span className="flex items-center gap-2">
      <CircleAlert color="#DC182C" className="size-4" /> Grading failed
    </span>
  ),
  automatically_graded: (
    <span className="flex items-center gap-2">
      <TriangleAlert color="green" className="size-4" /> Graded
    </span>
  ),
  not_graded: (
    <span className="flex items-center gap-2">
      <TriangleAlert color="#C77700" className="size-4" /> Not graded
    </span>
  )
};

const feedbackLabel: Record<FeedbackStatus, React.ReactNode> = {
  not_generated: (
    <span className="flex items-center gap-2">
      <OctagonAlert color="#DC182C" className="size-4" /> Not Feedback
    </span>
  ),
  generated: (
    <span className="flex items-center gap-2">
      <CircleCheck color="#6A9816" className="size-4" /> Generated
    </span>
  ),
  generating: (
    <span className="flex items-center gap-2">
      <CircleAlert color="#DC182C" className="size-4" /> Generating
    </span>
  ),

  generation_failed: (
    <span className="flex items-center gap-2">
      <TriangleAlert color="#C77700" className="size-4" /> Generation failed
    </span>
  ),
  feedback_outdated: (
    <span className="flex items-center gap-2">
      <TriangleAlert color="#C77700" className="size-4" /> Feedback outdated
    </span>
  )
};

type ColumnHandlers = {
  onViewDetails: (row: SubmissionRow) => void;
  onViewLogs?: (row: SubmissionRow) => void;
};

const getColumns = ({
  onViewDetails,
  onViewLogs
}: ColumnHandlers): Array<DataTableColumnDef<SubmissionRow>> => [
  expanderColumn<SubmissionRow>(),
  selectColumn<SubmissionRow>(),
  {
    accessorKey: 'studentName',
    header: 'Name',
    filterFn: 'filterFn_includesString',
    cell: ({ row, getValue }) => (
      <div className={row.depth > 0 ? 'flex items-center gap-6' : ''}>
        {row.depth > 0 && <RowCheckbox row={row} />}
        <span className="truncate">
          {row.depth > 0 ? row.original.label : getValue<string>()}
        </span>
      </div>
    )
  },
  {
    accessorKey: 'score',
    header: 'Final score',
    enableGlobalFilter: false,
    cell: ({ getValue }) => {
      const score = getValue<number | undefined>() || 0;
      return score === undefined ? null : `${score.toFixed(2)} / 800`;
    }
  },
  {
    accessorKey: 'gradingStatus',
    header: 'Auto Grading',
    enableGlobalFilter: false,
    filterFn: 'filterFn_includesString',
    cell: ({ getValue }) => {
      const grading = getValue<AutoStatus | undefined>();
      return grading ? gradingLabel[grading] : null;
    }
  },
  {
    accessorKey: 'feedbackStatus',
    header: 'Feedback',
    enableGlobalFilter: false,
    filterFn: 'filterFn_includesString',
    cell: ({ getValue }) => {
      const feedbackStatus = getValue<FeedbackStatus>();
      return feedbackStatus ? feedbackLabel[feedbackStatus] : null;
    }
  },
  {
    id: 'actions',
    header: 'Actions',
    enableGlobalFilter: false,
    cell: ({ row }) =>
      row.original.submission === undefined ? null : (
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            title="View submission details"
            aria-label="View submission details"
            onClick={() => onViewDetails(row.original)}
            ml-1
          >
            <Eye color="#006699" className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="View logs"
            aria-label="View logs"
            onClick={() => onViewLogs?.(row.original)}
          >
            <History color="#006699" className="size-4" />
          </Button>
        </div>
      )
  }
];

// table

type TTableProps = {
  submissions: Array<Submission> | null;
  grading: string;
  search?: string;
  setSearch: (val: string) => void;
  rowSelection: RowSelectionState;
  onRowSelectionChange: OnChangeFn<RowSelectionState>;
  columnFilters: ColumnFiltersState;
};

const SubmissionsDataTable = ({
  submissions,
  search,
  setSearch,
  rowSelection,
  onRowSelectionChange,
  columnFilters
}: TTableProps) => {
  const [selected, setSelected] = useState<Submission | null>(null);

  const data = useMemo(() => toSubmissionRows(submissions), [submissions]);

  const columns = useMemo(
    () =>
      getColumns({ onViewDetails: row => setSelected(row.submission ?? null) }),
    []
  );

  return (
    <div className="space-y-4 relative">
      <NestedTable
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

      <SubmissionDetailsDialog
        submission={selected}
        onClose={() => setSelected(null)}
      />
    </div>
  );
};

export default SubmissionsDataTable;
