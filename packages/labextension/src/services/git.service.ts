import { RepoType } from '../app/components/utils/repo-type';
import { request } from './request.service';
import { baseUrl } from './file.service';
import { HTTPMethod } from './enums/http-methods.enum';
import { Submission } from '../model/submission';

export function releaseAssignment(
  lectureId: number,
  assignmentId: number,
  repoType: RepoType,
  commitMessage?: string,
  selectedFiles?: string[]
): Promise<void> {
  let url = `${baseUrl({ lectureId, assignmentId })}push/${repoType}`;
  if (commitMessage) {
    const searchParams = new URLSearchParams({
      'commit-message': commitMessage
    });
    url += '?' + searchParams;
  }

  if (selectedFiles && selectedFiles.length > 0) {
    selectedFiles.forEach(file => {
      url += `&selected-files=${encodeURIComponent(file)}`;
    });
  }

  return request<void>(HTTPMethod.PUT, url, null);
}

export function pullAssignment(
  lectureId: number,
  assignmentId: number,
  repoType: RepoType
): Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}pull/${repoType}`,
    null
  );
}

export function submitAssignment(lectureId: number, assignmentId: number) {
  let url = `${baseUrl({ lectureId, assignmentId })}push/${RepoType.USER}`;
  const searchParams = new URLSearchParams({
    submit: 'true'
  });
  url += '?' + searchParams;

  return request<Submission>(HTTPMethod.PUT, url, null);
}

export function resetAssignment(
  lectureId: number,
  assignmentId: number
): Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}reset`,
    null
  );
}

export function getGitLogs(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  reload = false
): Promise<string> {
  const url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/${submissionId}/logs`;
  return request<string>(HTTPMethod.GET, url, null, reload);
}

export function createOrOverrideEditRepository(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<Submission> {
  const url = `${baseUrl({
    lectureId,
    assignmentId
  })}submissions/${submissionId}/edit`;
  return request<Submission>(HTTPMethod.PUT, url, {});
}

export async function pullFeedback(
  lectureId: number,
  assignmentId: number,
  submission: Submission
) {
  return request<void>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}grading/${submission.id}/pull/${
      RepoType.FEEDBACK
    }`,
    null
  );
}

export async function pullSubmissionFiles(
  lectureId: number,
  assignmentId: number,
  submission: Submission
) {
  let url = `${baseUrl({ lectureId, assignmentId })}pull/${RepoType.EDIT}`;

  const searchParams = new URLSearchParams({
    subid: String(submission.id)
  });
  url += '?' + searchParams;
  return request<void>(HTTPMethod.GET, url, null);
}

export async function createSubmissionFiles(
  lectureId: number,
  assignmentId: number,
  username: string
) {
  let url = `${baseUrl({ lectureId, assignmentId })}push/${RepoType.EDIT}`;
  const searchParams = new URLSearchParams({
    for_user: username
  });
  url += '?' + searchParams;
  return request<void>(HTTPMethod.PUT, url, null);
}

export async function pushSubmissionFiles(
  lectureId: number,
  assignmentId: number,
  submission: Submission
) {
  let url = `${baseUrl({ lectureId, assignmentId })}push/${RepoType.EDIT}`;
  const searchParams = new URLSearchParams({
    subid: String(submission.id)
  });
  url += '?' + searchParams;
  return request<void>(HTTPMethod.PUT, url, null);
}

export function restoreSubmission(
  lectureId: number,
  assignmentId: number,
  commitHash: string
): Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}restore/${commitHash}`,
    null
  );
}
