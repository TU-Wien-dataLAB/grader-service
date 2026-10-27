import { queryOptions } from '@tanstack/react-query';
import { getSubmissions } from '../submissions.service';

export const getAllSubmissions = (lectureId: number, assignmentId: number) =>
  queryOptions({
    queryKey: ['submissions'],
    queryFn: async () => getSubmissions(lectureId, assignmentId)
  });
