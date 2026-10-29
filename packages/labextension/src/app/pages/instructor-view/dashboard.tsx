import { SearchField } from '../../components/ui/search';
import { FilterLecturesButton } from '../../components/ui/filter-button';
import { SortButton } from '../../components/ui/sort-button';
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLectures } from '../../../services/lectures.service';
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
import { pluralize } from '../../components/utils/utils';
import { lecturesQuery } from '../../../services/queries/lectures.queries';
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
import { queryClient, useMutationStatus } from '../../../widget';
import { ErrorBanner } from '../../components/ui/error-banner';
import {
  lectureBasePath,
  openInFileBrowser
} from '../../../services/local-file.service';

export const Dashboard = () => {
  const [view, setView] = useState('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterBy, setFilterBy] = useState('');
  const [sortBy, setSortBy] = useState({ key: 'created_at', dir: 'asc' });
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(6);
  const { data: lecturesData } = useQuery(
    lecturesQuery(
      true,
      filterBy === 'completed',
      sortBy.key,
      sortBy.dir,
      page,
      perPage,
      searchQuery
    )
  );
  // fetching directly in the component, since fetching is conditional
  const {
    data: completedLectures,
    isPending: isPendingCompletedLectures,
    isRefetching: isRefetchingCompletedLectures
  } = useQuery({
    queryKey: ['completedLectures'],
    queryFn: async () => getLectures({ instructor: true, complete: true }),
    // only fetch completed lectures if the "completed" filter option has been chosen
    enabled: filterBy === 'completed'
  });

  useEffect(() => {
    openInFileBrowser(`${lectureBasePath}`);
  }, []);

  useEffect(() => {
    if (filterBy || searchQuery || sortBy.key) {
      queryClient.invalidateQueries({ queryKey: ['lectures'] });
    }
  }, [
    lecturesData,
    completedLectures,
    searchQuery,
    filterBy,
    sortBy,
    perPage,
    page,
    isPendingCompletedLectures,
    isRefetchingCompletedLectures
  ]);

  const { status } = useMutationStatus();
  const lectures = lecturesData?.lectures ?? [];

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
        <div
          className={
            'flex flex-col gap-2 justify-between items-center self-stretch @xl:flex-row @xl:gap-0'
          }
        >
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
            <span className={'font-bold'}>{lectures.length}</span>{' '}
            {pluralize({
              text: 'result',
              data: lectures.length
            })}{' '}
            found for <span className={'font-bold'}>"{searchQuery}"</span>
          </p>
        )}
      </div>
      {(lectures.length ?? 0) > 0 ? (
        lectures.length === 0 ? (
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
                {lectures?.map(lecture => (
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
                    {lectures.map(lecture => (
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
                    <PaginationFirst
                      isActive={page !== 1}
                      onClick={() => setPage(1)}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationPrevious
                      isActive={page !== 1}
                      onClick={() => setPage(prev => prev - 1)}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    {Array.from(
                      { length: lecturesData.total_pages },
                      (_, i) => (
                        <PaginationLink key={i} onClick={() => setPage(i + 1)}>
                          {i + 1}
                        </PaginationLink>
                      )
                    )}
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext
                      isActive={page !== lecturesData.total_pages}
                      onClick={() => setPage(prev => prev + 1)}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationLast
                      isActive={page !== lecturesData.total_pages}
                      onClick={() => setPage(lecturesData.total_pages)}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
              <Select value={perPage} onValueChange={setPerPage}>
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
            ' again later.'
          }
        />
      )}
    </div>
  );
};
