import { HTTPMethod } from './enums/http-methods.enum';
import { request } from './request.service';
import { Submission } from '../model/submission';
import { baseUrl } from './file.service';

export function getSubmissions(
  lectureId: number,
  assignmentId: number,
  filter: 'none' | 'latest' | 'best' = 'none',
  instructor = true,
  reload = false
): Promise<Submission[]> {
  let url = `${baseUrl({ lectureId, assignmentId })}submissions`;

  if (filter || instructor) {
    const searchParams = new URLSearchParams({
      'instructor-version': String(instructor),
      filter: filter
    });
    url += '?' + searchParams.toString();
  }
  return request<Submission[]>(HTTPMethod.GET, url, null, reload);
}

export function saveSubmissions(
  lectureId: number,
  assignmentId: number,
  filter: 'none' | 'latest' | 'best' = 'none'
): Promise<any> {
  let url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/save`;
  if (filter) {
    const searchParams = new URLSearchParams({
      filter: filter
    });
    url += '?' + searchParams.toString();
  }
  return request<any>(HTTPMethod.PUT, url, null);
}

export function getSubmission(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  reload: boolean = false
): Promise<Submission> {
  const url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/${submissionId}`;
  return request<Submission>(HTTPMethod.GET, url, null, reload);
}

export function updateSubmission(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  updatedSubmission: Submission
): Promise<Submission> {
  const url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/${submissionId}`;
  return request<Submission>(HTTPMethod.PUT, url, updatedSubmission);
}

export function deleteSubmission(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<void> {
  return request<void>(
    HTTPMethod.DELETE,
    `${baseUrl({ lectureId, assignmentId })}submissions/${submissionId}`,
    null
  );
}

export function getFeedback(
  lectureId: number,
  assignmentId: number,
  latest = false,
  instructor = false
): Promise<any> {
  let url = `${baseUrl({ lectureId, assignmentId })}feedback`;
  if (latest || instructor) {
    const searchParams = new URLSearchParams({
      'instructor-version': String(instructor),
      latest: String(latest)
    });
    url += '?' + searchParams.toString();
  }
  return request<any>(HTTPMethod.GET, url, null);
}

export function getProperties(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  reload = false
): Promise<any> {
  const url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/${submissionId}/properties`;
  return request<any>(HTTPMethod.GET, url, null, reload);
}

export function updateProperties(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  updatedProperties: any
): Promise<Submission> {
  const url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/${submissionId}/properties`;
  return request<Submission>(HTTPMethod.PUT, url, updatedProperties);
}

export function ltiSyncSubmissions(
  lectureId: number,
  assignmentId: number,
  option: string,
  submissionIds: number[] = []
): Promise<{
  synced_platforms: Array<{
    platform: string;
    syncable_users: number;
    synced_user: number;
  }>;
}> {
  let url = `${baseUrl({ lectureId, assignmentId })}submissions/lti`;
  const searchParams = new URLSearchParams({
    option: option
  });
  url += '?' + searchParams.toString();
  return request<{
    synced_platforms: Array<{
      platform: string;
      syncable_users: number;
      synced_user: number;
    }>;
  }>(HTTPMethod.PUT, url, { submission_ids: submissionIds });
}

export async function getSubmissionCount(
  lectureId: number,
  assignmentId: number
): Promise<{ submission_count: number }> {
  const url = `${baseUrl({ lectureId, assignmentId })}submissions/count`;
  return request<{ submission_count: number }>(
    HTTPMethod.GET,
    url,
    null,
    false
  );
}

export async function exportGrades(
  lectureId: number,
  filter: 'latest' | 'best' = 'best',
  format: 'json' | 'csv' = 'csv'
): Promise<any> {
  let url = `/api/lectures/${lectureId}/submissions`;
  const searchParams = new URLSearchParams({
    filter: filter,
    format: format
  });
  url += '?' + searchParams.toString();
  return request<any>(HTTPMethod.GET, url, null);
}
