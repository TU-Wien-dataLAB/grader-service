import { getLectures, getLecture, getLectureUsers } from '../lectures.service';
import { queryOptions } from '@tanstack/react-query';
import { useLectureFilters } from '../../app/stores/lecture-filter-store';
import { useShallow } from 'zustand/react/shallow';

export const lecturesQuery = (instructor: boolean = false) => {
  const { filterBy, sortBy, page, perPage, searchQuery } = useLectureFilters(
    useShallow(s => ({
      filterBy: s.filterBy,
      sortBy: s.sortBy,
      page: s.page,
      perPage: s.perPage,
      searchQuery: s.searchQuery
    }))
  );
  const key = sortBy.key;
  const dir = sortBy.dir;
  return queryOptions({
    queryKey: [
      'lectures',
      { instructor, filterBy, key, dir, page, perPage, searchQuery }
    ],
    queryFn: () =>
      getLectures(
        {
          complete: filterBy === 'completed',
          sort_by: sortBy.key,
          order: sortBy.dir,
          search: searchQuery
        },
        instructor,
        page,
        perPage
      )
  });
};

export const lectureQuery = (lectureId: number) =>
  queryOptions({
    queryKey: ['lectures', lectureId],
    queryFn: async () => getLecture(lectureId, false)
  });

export const lectureUsersQuery = (lectureId: number) =>
  queryOptions({
    queryKey: ['lectureUsers', lectureId],
    queryFn: async () => getLectureUsers(lectureId, false)
  });
