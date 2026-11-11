import { queryOptions } from '@tanstack/react-query';
import {
  exportGrades,
  getSubmission,
  getSubmissionLogs,
  getSubmissions
} from '../submissions.service';
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
    queryFn: async () =>
      getSubmission(lectureId, assignmentId, submissionId, true)
  });

export const getPulledSubmissionFiles = (
  lectureId: number,
  assignmentId: number,
  submissionId: number
) =>
  queryOptions({
    queryKey: ['submissionFiles', submissionId],
    queryFn: async () =>
      pullSubmissionFiles(lectureId, assignmentId, submissionId)
  });

export const getSubmissionLogsData = (
  lectureId: number,
  assignmentId: number,
  submissionId: number
) =>
  queryOptions({
    queryKey: ['submissionLogs', submissionId],
    queryFn: async () =>
      getSubmissionLogs(lectureId, assignmentId, submissionId)
  });

export const exportSubmissionsData = (
  lectureId: number,
  filter: 'latest' | 'best' = 'best',
  format: 'json' | 'csv' = 'csv'
) =>
  queryOptions({
    queryKey: ['exportSubmissions'],
    queryFn: async () => exportGrades(lectureId, filter, format)
  });
