import React, { useEffect, useMemo, useState } from 'react';
import { SearchField } from '../../ui/search';
import { Button } from '../../../shadcn-components/ui/button';
import { SubmissionsActions } from './submissions-actions';
import { FilterSubmissionsButton, IFilterGroup } from '../../ui/filter-button';
import { ColumnFiltersState, RowSelectionState } from '@tanstack/react-table';
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
import { Badge } from '../../../shadcn-components/ui/badge';
import { X } from 'lucide-react';
import { queryClient, useMutationStatus } from '../../../../widget';
import { SuccessBanner } from '../../ui/success-banner';
import { useMutation, useQuery } from '@tanstack/react-query';
import { getAllSubmissions } from '../../../../services/queries/submissions.query';
import {
  lectureBasePath,
  openInFileBrowser
} from '../../../../services/local-file.service';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import {
  autogradeSubmission,
  generateFeedback
} from '../../../../services/grading.service';
import { ErrorBanner } from '../../ui/error-banner';

type TProps = {
  setOpenNewSubmission: (val: boolean) => void;
  lectureId: number;
  assignmentId: number;
};

export const SubmissionsView = (props: TProps) => {
  const { lectureId, assignmentId, setOpenNewSubmission } = props;
  const [searchQuery, setSearchQuery] = useState('');
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [activeFilters, setActiveFilters] = useState(new Set<string>());
  const { status, setStatus } = useMutationStatus();

  const { data: lecture } = useQuery(lectureQuery(lectureId));
  const path = `${lectureBasePath}${lecture.code}/edit/${assignmentId}`;

  // used for checking/unchecking a checkbox
  const toggle = (key: string, value: string, label: string) => {
    const id = `${key}:${value}:${label}`;
    setActiveFilters(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const columnFilters = useMemo<ColumnFiltersState>(() => {
    const gradingFilterValues: string[] = [];
    const feedbackFilterValues: string[] = [];
    Array.from(activeFilters).forEach(id => {
      const [key, value] = id.split(':');
      if (key === 'Grading') gradingFilterValues.push(value);
      if (key === 'Feedback') feedbackFilterValues.push(value);
    });
    return [
      ...(searchQuery ? [{ id: 'name', value: searchQuery }] : []),
      ...(gradingFilterValues.length
        ? [{ id: 'gradingStatus', value: gradingFilterValues }]
        : []),
      ...(feedbackFilterValues.length
        ? [{ id: 'feedbackStatus', value: feedbackFilterValues }]
        : [])
    ];
  }, [searchQuery, activeFilters]);

  const {
    data: submissionsList,
    refetch,
    isLoading
  } = useQuery(getAllSubmissions(lectureId, assignmentId));

  const STATIC_FILTERS: IFilterGroup[] = [
    {
      Grading: [
        {
          value: 'pending',
          label: 'Pending'
        },
        { value: 'automatically_graded', label: 'Automatically graded' },
        {
          value: 'not_graded',
          label: 'Not graded'
        },
        {
          value: 'grading_failed',
          label: 'Grading failed'
        }
      ],
      Feedback: [
        { value: 'generated', label: 'Feedback given' },
        { value: 'not_generated', label: 'No feedback' },
        { value: 'generation_failed', label: 'Feedback failed' }
      ]
    }
  ];

  useEffect(() => {
    openInFileBrowser(path);
  }, [path]);

  const generateFeedbackMutation = useMutation({
    mutationFn: async () => {
      await Promise.all(
        Object.keys(rowSelection).map(submissionId =>
          generateFeedback(lectureId, assignmentId, Number(submissionId))
        )
      );
    },
    onSuccess: () => {
      setStatus({
        message:
          'You successfully generated feedback for selected submissions!',
        status: 'success'
      });
      queryClient.invalidateQueries({
        queryKey: ['submissions']
      });
      setRowSelection({});
    },
    onError: () => {
      setStatus({
        message: 'Failed to generate a feedback. Please, try again!',
        status: 'error'
      });
    }
  });

  const autogradeMutation = useMutation({
    mutationFn: async () => {
      await Promise.all(
        Object.keys(rowSelection).map(submissionId =>
          autogradeSubmission(lectureId, assignmentId, Number(submissionId))
        )
      );
    },
    onSuccess: () => {
      setStatus({
        message: 'You successfully autograded selected submissions!',
        status: 'success'
      });
      queryClient.invalidateQueries({
        queryKey: ['submissions']
      });
      setRowSelection({});
    },
    onError: () => {
      setStatus({
        message: 'Failed to autograde. Please, try again!',
        status: 'error'
      });
    }
  });

  if (isLoading) {
    return <h1>Loading...</h1>;
  }

  return (
    <div className={'flex flex-col items-start gap-4 self-stretch'}>
      {status.status === 'success' && (
        <SuccessBanner message={status.message} />
      )}
      {status.status === 'error' && <ErrorBanner message={status.message} />}
      <div className={'flex justify-between items-center self-stretch'}>
        <h2 className={'text-xl font-bold'}>Submissions</h2>
        <div className="flex gap-3">
          <Button onClick={() => refetch()} variant={'outline'}>
            Reload
          </Button>
          <SubmissionsActions setOpenNewSubmission={setOpenNewSubmission} />
        </div>
      </div>
      <div className={'flex justify-between items-center self-stretch'}>
        <SearchField
          placeholder="Search for submissions"
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
        <FilterSubmissionsButton
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
        <div className="overflow-auto h-fit max-h-[700px]">
          <SubmissionsDataTable
            submissions={submissionsList}
            columnFilters={columnFilters}
            rowSelection={rowSelection}
            onRowSelectionChange={setRowSelection}
            setSearch={setSearchQuery}
            search={searchQuery}
          />
        </div>

        <div className="flex items-center justify-between gap-4 mt-2">
          <p className="whitespace-nowrap">
            10 out of {submissionsList?.length || 0}
          </p>
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
        <Button onClick={() => autogradeMutation.mutate()}>Autograde</Button>
        <Button
          onClick={() => generateFeedbackMutation.mutate()}
          variant="outline"
        >
          Generate feedback
        </Button>
      </div>
    </div>
  );
};
