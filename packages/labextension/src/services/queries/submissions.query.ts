import { queryOptions } from '@tanstack/react-query';
import { getSubmission, getSubmissions } from '../submissions.service';
import { pullSubmissionFiles } from '../git.service';

export const getAllSubmissions = (lectureId: number, assignmentId: number) =>
  queryOptions({
    queryKey: ['submissions'],
    queryFn: async () => getSubmissions(lectureId, assignmentId)
  });

export const getSubmissionById = (
  lectureId: number,
  assignmentId: number,
  submissionId: number
) =>
  queryOptions({
    queryKey: ['submissionById', submissionId],
    queryFn: async () => getSubmission(lectureId, assignmentId, submissionId)
  });

export const getPulledSubmissionFiles = (
  lectureId: number,
  assignmentId: number,
  submissionId: number
) =>
  queryOptions({
    queryKey: ['submissionFilesl', submissionId],
    queryFn: async () =>
      pullSubmissionFiles(lectureId, assignmentId, submissionId)
  });
