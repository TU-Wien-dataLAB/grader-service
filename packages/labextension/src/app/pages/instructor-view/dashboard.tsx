import { SearchField } from '../../components/ui/search';
import { FilterLecturesButton } from '../../components/ui/filter-button';
import { SortButton } from '../../components/ui/sort-button';
import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAllLectures } from '../../../services/lectures.service';
import { LayoutGrid, List } from 'lucide-react';
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow
} from '../../shadcn-components/ui/table';
import { LectureCard } from '../../components/grader-service/lectures/lecture-card';
import { LectureRow } from '../../components/grader-service/lectures/lecture-row';
import { determineDisplayText } from '../../components/utils/utils';
import { activeInstructorLecturesQuery } from '../../../services/queries/lectures.queries';
import { Header } from '../../components/ui/header';
import {
  ToggleGroup,
  ToggleGroupItem
} from '../../shadcn-components/ui/toggle-group';
import {
  Pagination,
  PaginationContent,
  PaginationFirst,
  PaginationItem,
  PaginationLast,
  PaginationLink,
  PaginationNext,
  PaginationPrevious
} from '../../shadcn-components/ui/pagination';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../shadcn-components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../shadcn-components/ui/tooltip';
import { SuccessBanner } from '../../components/ui/success-banner';
import { NoResultsFoundIcon } from '../../../assets/no-results-found-icon';
import { EmptyIcon } from '../../../assets/empty-icon';
import { EmptyState } from '../../components/utils/empty-state';
import { useMutationStatus } from '../../../widget';
import { ErrorBanner } from '../../components/ui/error-banner';

export const Dashboard = () => {
  const [view, setView] = useState('grid');
  const { data: lectures } = useQuery(activeInstructorLecturesQuery());

  const [searchQuery, setSearchQuery] = useState('');
  const [filterBy, setFilterBy] = useState('');
  const [sortBy, setSortBy] = useState({ key: '', dir: '' });
  // fetching directly in the component, since fetching is conditional
  const {
    data: completedLectures,
    isPending: isPendingCompletedLectures,
    isRefetching: isRefetchingCompletedLectures
  } = useQuery({
    queryKey: ['completedLectures'],
    queryFn: async () =>
      getAllLectures({ instructor: true, complete: true }, false),
    // only fetch completed lectures if the "completed" filter option has been chosen
    enabled: filterBy === 'completed'
  });
  /* logic for searching/filtering/sorting */
  const filteredLectures = useMemo(() => {
    if (!lectures) {
      return [];
    }

    let result = [...lectures];

    if (filterBy) {
      if (filterBy === 'completed' && !isPendingCompletedLectures) {
        result = [...completedLectures];
      }
    }
    if (searchQuery) {
      result = result.filter(
        l =>
          l.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          l.code?.toLowerCase().includes(searchQuery.toLowerCase())
      );
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
    lectures,
    completedLectures,
    searchQuery,
    filterBy,
    sortBy,
    isPendingCompletedLectures,
    isRefetchingCompletedLectures
  ]);

  const { status } = useMutationStatus();

  return (
    <div
      className={'flex h-full flex-col w-full overflow-hidden bg-background'}
      id={'lecture-view'}
    >
      <Header />
      <div className={'flex flex-col sticky top-0 shrink-0 m-6 gap-6'}>
        <span className={'text-xl font-bold'}>Courses</span>
        {status.status === 'success' && (
          <SuccessBanner message={status.message} />
        )}
        {status.status === 'error' && <ErrorBanner message={status.message} />}
        <div className={'flex justify-between items-center self-stretch'}>
          <SearchField
            placeholder={'Search for course'}
            recentSearchesKey={'lecture-search-history'}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
          <div className={'flex flex-row ml-auto gap-3'}>
            <FilterLecturesButton
              filterBy={filterBy}
              setFilterBy={setFilterBy}
            />
            <SortButton sortBy={sortBy} setSortBy={setSortBy} />
            <ToggleGroup type={'single'}>
              <Tooltip>
                <TooltipTrigger
                  render={
                    <span>
                      <ToggleGroupItem
                        value={'grid'}
                        onClick={() => setView('grid')}
                        variant={view === 'grid' ? 'default' : 'outline'}
                        className={'p-4'}
                      >
                        <LayoutGrid className={'size-4 fill-secondary'} />
                      </ToggleGroupItem>
                    </span>
                  }
                />
                <TooltipContent>
                  <p>Show as grid</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger
                  render={
                    <span>
                      <ToggleGroupItem
                        value={'list'}
                        onClick={() => setView('list')}
                        variant={view === 'list' ? 'default' : 'outline'}
                        className={'p-4'}
                      >
                        <List className={'size-4'} />
                      </ToggleGroupItem>
                    </span>
                  }
                />
                <TooltipContent>
                  <p>Show as list</p>
                </TooltipContent>
              </Tooltip>
            </ToggleGroup>
          </div>
        </div>
        {searchQuery && (
          <p className={'w-fit'}>
            <span className={'font-bold'}>{filteredLectures.length}</span>{' '}
            {determineDisplayText({
              text: 'result',
              data: filteredLectures
            })}{' '}
            found for <span className={'font-bold'}>"{searchQuery}"</span>
          </p>
        )}
      </div>
      {(lectures?.length ?? 0) > 0 ? (
        filteredLectures.length === 0 ? (
          <EmptyState
            title={'No results found'}
            icon={<NoResultsFoundIcon />}
            description={
              'Try adjusting your search or ' +
              "filter to find what \n you're looking for."
            }
          />
        ) : (
          <div
            className={
              'flex flex-col gap-6 m-6 mt-0 overflow-y-auto min-h-0 flex-1 h-full'
            }
          >
            {view === 'grid' && (
              <div
                className={
                  'grid gap-6 grid-cols-1 @3xl:grid-cols-2 @6xl:grid-cols-3' //defining grid like this is necessary to have responsive window from both sides
                }
              >
                {filteredLectures?.map(lecture => (
                  <LectureCard lecture={lecture} searchQuery={searchQuery} />
                ))}
              </div>
            )}
            {view === 'list' && (
              <div className={'w-full overflow-x-auto'}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Assignments</TableHead>
                      <TableHead>Students</TableHead>
                      <TableHead></TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLectures.map(lecture => (
                      <LectureRow lecture={lecture} searchQuery={searchQuery} />
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            <div className="flex items-center justify-between gap-4">
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
                      { length: Math.ceil(lectures.length / 6) },
                      (_, i) => (
                        <PaginationLink>{i + 1}</PaginationLink>
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
              <Select defaultValue="6">
                <SelectTrigger id="select-rows-per-page">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent align="start">
                  <SelectGroup>
                    <SelectItem value="4">4 / Page</SelectItem>
                    <SelectItem value="6">6 / Page</SelectItem>
                    <SelectItem value="8">8 / Page</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>
          </div>
        )
      ) : (
        <EmptyState
          title={'No courses yet'}
          icon={<EmptyIcon />}
          description={
            'There are no courses available for you right \n now. Please check' +
            'again later.'
          }
        />
      )}
    </div>
  );
};
