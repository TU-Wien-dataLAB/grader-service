import React, {
  useEffect,
  useMemo,
  useState
} from 'react';
import { useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { Button } from '../../shadcn-components/ui/button';
import { SearchField } from '../../components/ui/search';
import {
  FilterAssignmentsButton,
  IFilterGroup,
} from '../../components/ui/filter-button';
import { SortButton } from '../../components/ui/sort-button';
import { Assignment } from '../../../model/assignment';
import { lectureQuery } from '../../../services/queries/lectures.queries';
import { assignmentsQuery } from '../../../services/queries/assignments.queries';
import { useMutationStatus } from '../../../widget';
import { SuccessBanner } from '../../components/ui/success-banner';
import { ErrorBanner } from '../../components/ui/error-banner';
import { Badge } from '../../shadcn-components/ui/badge';
import { EmptyIcon } from '../../../assets/empty-icon';
import { EmptyState } from '../../components/utils/empty-state';
import { NoResultsFoundIcon } from '../../../assets/no-results-found-icon';
import { X } from 'lucide-react';
import { AssignmentCardStudent } from '../../components/grader-service/assignments/assignment-card-student';
import { lectureBasePath, openInFileBrowser } from '../../../services/local-file.service';


const STATIC_FILTERS_STUDENT: IFilterGroup[] = [
  {
    Status: [
      { value: 'All', label: 'All' },
      { value: 'In progress', label: 'In progress' },
      { value: 'Feedback', label: 'Feedback' },
      { value: 'Changes', label: 'Changes' },
      { value: 'New', label: 'New' }
    ],
        Deadline: [
      { value: 'Deadline over', label: 'Deadline over' },
      { value: 'Upcoming', label: 'Upcoming' },
      { value: 'No Deadline', label: 'No Deadline' }
    ],
  }
];


export const Lecture = () => {
  const params = useParams();
  const lectureId = Number(params.id);

  const { data: lecture, isPending: isPendingLecture } = useQuery(
    lectureQuery(lectureId)
  );

  useEffect(() => {
    openInFileBrowser(`${lectureBasePath}${lecture.code}`);
  });


  const {
    data: assignments,
    isPending: isPendingAssignments,
    isRefetching: isRefetchingAssignments
  } = useQuery(assignmentsQuery(lectureId));

  // filtering logic
  const [sortBy, setSortBy] = useState({ key: '', dir: '' });
  const [searchQuery, setSearchQuery] = useState('');

  const allFilters = useMemo(() => {
    if (isPendingAssignments) {
      return [];
    }
    
    return [...STATIC_FILTERS_STUDENT];
  }, [assignments, isPendingAssignments]);

  // active filters are set as key:value:label
  const [activeFilters, setActiveFilters] = useState(new Set<string>());
  // used for checking/unchecking a checkbox
  const toggle = (key: string, value: string, label: string) => {
    const id = `${key}:${value}:${label}`;
    setActiveFilters(prev => {
      const next = new Set(prev);
      // eslint-disable-next-line @typescript-eslint/no-unused-expressions
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // search, filter and sort function
  const filteredAssignments = useMemo(() => {
    let result;

    if (isPendingAssignments) {
      return [];
    }

    result = [...assignments];
    if (searchQuery) {
      result = result.filter(a =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (activeFilters) {
      const currentDate = new Date();
      const activeGroups: Record<string, string[]> = {};
      for (const id of activeFilters) {
        const [key, value] = id.split(':');
        (activeGroups[key] ??= []).push(value);
      }

      if (activeGroups['Status']) {
        result = result.filter(a => activeGroups['Status'].includes(a.status));
      }


      if (activeGroups['Deadline']) {
        result = result.filter(a => {
          if (activeGroups['Deadline'].includes('No Deadline')) {
            return !a.settings.deadline;
          }
          const deadline = a.settings.deadline
            ? new Date(a.settings.deadline)
            : undefined;
          return activeGroups['Deadline'].some(v =>
            deadline && v === 'Overdue'
              ? deadline < currentDate
              : deadline > currentDate
          );
        });
      }

    }
    if (sortBy) {
      result = result.sort((a, b) => {
        const modifier = sortBy.dir === 'asc' ? 1 : -1;
        if (sortBy.key === 'name') {
          return (a.name ?? '').localeCompare(b.name ?? '') * modifier;
        }
        if (sortBy.key === 'date') {
          return (a.id - b.id) * modifier;
        }
        return 0;
      });
    }

    return result;
  }, [
    assignments,
    isPendingAssignments,
    isRefetchingAssignments,
    searchQuery,
    sortBy,
    activeFilters
  ]);

    // split assignments based on their group
    const groupsDict = useMemo(() => {
    const dict: Record<string, Assignment[]> = {};

    filteredAssignments.forEach(assignment => {
        const group = assignment.settings?.group;
        const key = group ? group : 'Ungrouped assignments';
        (dict[key] ??= []).push(assignment);
    });

    // ensure "ungrouped assignments" appears first, if present
    if (dict['ungrouped assignments']) {
        const { 'ungrouped assignments': ungrouped, ...rest } = dict;
        return { 'ungrouped assignments': ungrouped, ...rest };
    }

    return dict;
    }, [filteredAssignments]);


  const { status } = useMutationStatus();


  return (
      <div
        className={
          'flex flex-col bg-background items-start p-6 gap-6 self-stretch w-full h-full overflow-hidden'
        }
      >
        <div
          className={
            'flex flex-row sticky justify-between items-center self-stretch gap-2'
          }
        >
          {!isPendingLecture && (
            <div className={'flex flex-col gap-1 items-start min-w-0'}>
              <h1 className={'text-2xl w-full font-bold truncate'}>
                {lecture.name}
              </h1>
              <h3 className={'text-base font-bold'}>{lecture.code}</h3>
            </div>
          )}
        </div>
        {status.status === 'success' && (
          <SuccessBanner message={status.message} />
        )}
        {status.status === 'error' && <ErrorBanner message={status.message} />}
        {assignments.length > 0 && (
          <div className={'flex justify-between items-center self-stretch'}>
            <SearchField
              placeholder={'Search for assignment'}
              recentSearchesKey={'assignment-search-history'}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
            <div className={'flex flex-row ml-auto gap-3'}>
              <FilterAssignmentsButton
                allFilters={allFilters}
                activeFilters={activeFilters}
                toggle={toggle}
              />
              <SortButton 
                sortBy={sortBy} 
                setSortBy={setSortBy} 
              />
            </div>
          </div>
        )}
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
        {assignments.length > 0 ? (
          filteredAssignments.length > 0 ? (

          <div className="flex flex-col self-stretch overflow-y-auto">
            {Object.entries(groupsDict).map(([group, items]) => (
                <div key={group} className="flex flex-col gap-2 self-stretch mb-8">
                <h2 className="font-bold text-xl">
                    {group} ({items.length})
                </h2>
                <div className="grid grid-cols-1 @4xl:grid-cols-2 @7xl:grid-cols-3 gap-2">
                    {items.map(assignment => (
                    <AssignmentCardStudent
                        key={assignment.id}
                        assignment={assignment}
                    />
                    ))}
                </div>
                </div>
            ))}
            </div>

          ) : (
            <EmptyState
              title={'No results found'}
              icon={<NoResultsFoundIcon />}
              description={
                'Try adjusting your search or ' +
                "filter to find what \n you're looking for."
              }
            />
          )
        ) : (
          <div className={'flex flex-col items-center py-6 self-stretch'}>
            <EmptyState
              title={'No assignments yet'}
              icon={<EmptyIcon />}
              description={
                'Create a new assignment to distribute tasks and enable feedback.'
              }
            />
          </div>
        )}
      </div>

  );
};

