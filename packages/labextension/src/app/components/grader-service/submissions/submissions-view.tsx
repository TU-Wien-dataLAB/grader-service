import React, { useState } from 'react';
import { SearchField } from '../../ui/search';
import { Button } from '../../../shadcn-components/ui/button';
import { SubmissionsActions } from './submissions-actions';
import { FilterAssignmentsButton, IFilterGroup } from '../../ui/filter-button';
import { RowSelectionState } from '@tanstack/react-table';
import SubmissionsDataTable from './submissions-data-table';
import {
  Pagination,
  PaginationContent,
  PaginationFirst,
  PaginationItem,
  PaginationLast,
  PaginationLink,
  PaginationNext,
  PaginationPrevious
} from '../../../shadcn-components/ui/pagination';
import { Field } from '../../../shadcn-components/ui/field';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';
import { mockSubmissionsData } from './table-mock-data';
import { Badge } from '../../../shadcn-components/ui/badge';
import { X } from 'lucide-react';
import { useMutationStatus } from '../../../../widget';
import { SuccessBanner } from '../../ui/success-banner';

type TProps = {
  setOpenNewSubmission: (val: boolean) => void;
};

export const SubmissionsView = (props: TProps) => {
  type Grading = 'graded' | 'failed' | 'not_graded';
  const [searchQuery, setSearchQuery] = React.useState('');
  const [search, setSearch] = useState('');
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [grading, setGrading] = useState<'all' | Grading>('all');
  const { status } = useMutationStatus();

  console.log(() => setGrading('all'));

  const [activeFilters, setActiveFilters] = useState(new Set<string>());

  // used for checking/unchecking a checkbox
  const toggle = (key: string, value: string, label: string) => {
    const id = `${key}:${value}:${label}`;
    setActiveFilters(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const STATIC_FILTERS: IFilterGroup[] = [
    {
      Grading: [
        {
          value: '',
          label: 'Graded'
        },
        { value: '', label: 'Not graded' },
        {
          value: '',
          label: 'Grading failed'
        }
      ],
      Feedback: [
        { value: 'Overdue', label: 'Feedback given' },
        { value: 'Upcoming', label: 'No feedback' }
      ]
    }
  ];

  return (
    <div className={'flex flex-col items-start gap-4 self-stretch'}>
      {status.status === 'success' && (
        <SuccessBanner message={status.message} />
      )}
      <div className={'flex justify-between items-center self-stretch'}>
        <h2 className={'text-xl font-bold'}>Submissions</h2>
        <div className="flex gap-3">
          <Button variant={'outline'}>Reload</Button>
          <SubmissionsActions
            setOpenNewSubmission={props.setOpenNewSubmission}
          />
        </div>
      </div>
      <div className={'flex justify-between items-center self-stretch'}>
        <SearchField
          placeholder="Search for submissions"
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
        <FilterAssignmentsButton
          allFilters={STATIC_FILTERS}
          activeFilters={activeFilters}
          toggle={toggle}
        />
      </div>
      {activeFilters.size > 0 && (
        <div className={'flex flex-row gap-4 items-start'}>
          {Array.from(activeFilters).map(id => {
            const [key, value, label] = id.split(':');
            return (
              <div
                className={
                  'flex items-center gap-0.5 rounded-xs border border-muted-foreground'
                }
              >
                <Badge variant={'secondary'} className={'p-0 pl-2'}>
                  <span className={'font-bold'}>{key}</span>: {label}
                  <Button
                    variant={'link'}
                    onClick={() => toggle(key, value, label)}
                  >
                    <X className={'size-4'} aria-label={'Remove filter'} />
                  </Button>
                </Badge>
              </div>
            );
          })}
          <Button
            variant={'link'}
            aria-label={'Reset filters'}
            onClick={() => setActiveFilters(new Set())}
          >
            Reset filter
          </Button>
        </div>
      )}
      <div className="w-full">
        <SubmissionsDataTable
          submissions={mockSubmissionsData}
          grading={grading}
          columnFilters={activeFilters}
          rowSelection={rowSelection}
          onRowSelectionChange={setRowSelection}
          setSearch={setSearch}
          search={search}
        />
        <div className="flex items-center justify-between gap-4 mt-2">
          <p className="whitespace-nowrap">10 of 198</p>
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationFirst />
              </PaginationItem>
              <PaginationItem>
                <PaginationPrevious />
              </PaginationItem>
              <PaginationItem>
                {Array.from(
                  {
                    length: Math.ceil(Array(15).length / 6)
                  },
                  (_, i) => (
                    <PaginationLink key={i}>{i + 1}</PaginationLink>
                  )
                )}
              </PaginationItem>
              <PaginationItem>
                <PaginationNext />
              </PaginationItem>
              <PaginationItem>
                <PaginationLast />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
          <Field orientation="horizontal" className="w-fit">
            <Select defaultValue="25">
              <SelectTrigger className="w-20" id="select-rows-per-page">
                <SelectValue placeholder="Select amount">
                  {value => `${value || 10} / Page`}
                </SelectValue>
              </SelectTrigger>
              <SelectContent align="start">
                <SelectGroup>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="25">25 </SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
        </div>
      </div>
      <div className="flex gap-4">
        <Button>Autograde</Button>
        <Button variant="outline">Generate feedback</Button>
      </div>
    </div>
  );
};
