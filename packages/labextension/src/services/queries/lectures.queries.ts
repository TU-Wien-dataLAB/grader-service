import { getLectures, getLecture, getLectureUsers } from '../lectures.service';
import { queryOptions } from '@tanstack/react-query';

export const lecturesQuery = (
  instructor: boolean = false,
  complete: boolean = false,
  sort_by: string = null,
  order: string = 'asc',
  page: number = 1,
  per_page: number = 10,
  search: string = null
) =>
  queryOptions({
    queryKey: ['lectures', { instructor, complete }],
    queryFn: () =>
      getLectures(
        {
          complete: complete,
          sort_by: sort_by,
          order: order,
          search: search
        },
        instructor,
        page,
        per_page
      )
  });

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
