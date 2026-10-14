import { getLectures, getLecture } from '../lectures.service';
import { queryOptions } from '@tanstack/react-query';

export const activeInstructorLecturesQuery = () =>
  queryOptions({
    queryKey: ['activeLectures'],
    queryFn: async () =>
      getLectures({ instructor: true, complete: false }, false)
  });

export const completedLecturesQuery = () =>
  queryOptions({
    queryKey: ['completedLectures'],
    queryFn: async () =>
      getLectures({ instructor: true, complete: true }, false)
  });

export const activeLecturesQuery = () =>
  queryOptions({
    queryKey: ['lectures'],
    queryFn: async () =>
      getLectures({ instructor: false, complete: false }, false)
  });

export const lectureQuery = (lectureId: number) =>
  queryOptions({
    queryKey: ['lectures', lectureId],
    queryFn: async () => getLecture(lectureId, false)
  });
