import { SearchField } from '../../ui/search';
import { SortButton } from '../../ui/sort-button';
import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLectures } from '../../../../services/lectures.service';
import { LectureCard } from './lecture-card';
import { pluralize } from '../../utils/utils';
import { activeLecturesQuery } from '../../../../services/queries/lectures.queries';
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
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../../shadcn-components/ui/select';

import { SuccessBanner } from '../../../components/ui/success-banner';
import { NoResultsFoundIcon } from '../../../../assets/no-results-found-icon';
import { EmptyIcon } from '../../../../assets/empty-icon';
import { EmptyState } from '../../../components/utils/empty-state';
import { useMutationStatus } from '../../../../widget';
import { ErrorBanner } from '../../../components/ui/error-banner';

export const Courses = () => {
  const { data: lectures } = useQuery(activeLecturesQuery());

  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState({ key: '', dir: '' });
  // fetching directly in the component, since fetching is conditional
  const {
    data: completedLectures,
    isPending: isPendingCompletedLectures,
    isRefetching: isRefetchingCompletedLectures
  } = useQuery({
    queryKey: ['completedLectures'],
    queryFn: async () =>
      getLectures({ instructor: true, complete: true }, false),
  });
  /* logic for searching/filtering/sorting */
  const filteredLectures = useMemo(() => {
    if (!lectures) {
      return [];
    }

    let result = [...lectures];

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
    sortBy,
    isPendingCompletedLectures,
    isRefetchingCompletedLectures
  ]);

  const { status } = useMutationStatus();

  return (
    <div
      className={'flex h-full flex-col w-full overflow-hidden bg-background'}
      id={'courses-view'}
    >
      <div className={'flex flex-col sticky top-0 shrink-0 m-4 gap-6'}>
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
            <SortButton sortBy={sortBy} setSortBy={setSortBy} />
          </div>
        </div>
        {searchQuery && (
          <p className={'w-fit'}>
            <span className={'font-bold'}>{filteredLectures.length}</span>{' '}
            {pluralize({
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
          <>  
          <div
            className={
              'flex flex-col gap-6 m-4 mt-0 overflow-y-auto flex-1'
            }
          >

            <div
                className={
                'grid gap-6 grid-cols-1 @3xl:grid-cols-2 @6xl:grid-cols-3' //defining grid like this is necessary to have responsive window from both sides
                }
            >
                {filteredLectures?.map(lecture => (
                <LectureCard lecture={lecture} searchQuery={searchQuery} />
                ))}
            </div>

          </div>
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
        </>

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
