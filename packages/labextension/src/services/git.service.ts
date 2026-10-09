import { RepoType } from '../app/components/utils/repo-type';
import { request } from './request.service';
import { HTTPMethod } from './enums/http-methods.enum';
import { Submission } from '../model/submission';
import { Lecture } from '../model/lecture';
import { Assignment } from '../model/assignment';
import { RemoteFileStatus } from '../model/remoteFileStatus';

interface IGitLogObject {
  commit: string;
  author: string;
  date: string;
  ref: string;
  commit_msg: string;
  pre_commit: string;
}

export const baseUrl = (props: { lectureId: number; assignmentId: number }) => {
  return `/api/lectures/${props.lectureId}/assignments/${props.assignmentId}/`;
};

export function pushAssignment(
  lectureId: number,
  assignmentId: number,
  repoType: RepoType,
  commitMessage?: string,
  selectedFiles?: string[]
): Promise<void> {
  let url = `${baseUrl({ lectureId, assignmentId })}push/${repoType}`;

  const searchParams = new URLSearchParams();
  if (commitMessage) {
    searchParams.set('commit-message', commitMessage);
  }
  if (selectedFiles && selectedFiles.length > 0) {
    selectedFiles.forEach(file => searchParams.append('selected-files', file));
  }
  if (searchParams.size > 0) {
    url += '?' + searchParams.toString();
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
  username: string,
  selectedFiles: string[]
) {
  let url = `${baseUrl({ lectureId, assignmentId })}push/${RepoType.EDIT}`;
  const searchParams = new URLSearchParams({
    for_user: username
  });
  // selectedFiles.forEach(file => searchParams.append('selected_files', file));
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

/**
 * Returns the last n commits of the given repo
 */
export function getGitLog(
  lecture: Lecture,
  assignment: Assignment,
  repo: RepoType,
  nCommits: number
): Promise<IGitLogObject[]> {
  let url = `${baseUrl({
    lectureId: lecture.id,
    assignmentId: assignment.id
  })}log/${repo}/`;
  const searchParams = new URLSearchParams({
    n: String(nCommits)
  });
  url += '?' + searchParams;
  return request<IGitLogObject[]>(HTTPMethod.GET, url, null, true);
}

/**
 * Returns the status of the given repo
 */
export function getRemoteStatus(
  lecture: Lecture,
  assignment: Assignment,
  repo: RepoType,
  reload = false
): Promise<RemoteFileStatus> {
  const url = `${baseUrl({
    lectureId: lecture.id,
    assignmentId: assignment.id
  })}remote-status/${repo}/`;
  return request<RemoteFileStatus>(HTTPMethod.GET, url, null, reload);
}

/**
 * Returns the status of the given file in the given repo
 */
export function getRemoteFileStatus(
  lecture: Lecture,
  assignment: Assignment,
  repo: RepoType,
  filePath: string,
  reload = false
): Promise<RemoteFileStatus> {
  const url = `${baseUrl({
    lectureId: lecture.id,
    assignmentId: assignment.id
  })}/remote-file-status/${repo}/?file=${encodeURIComponent(filePath)}`;
  return request<RemoteFileStatus>(HTTPMethod.GET, url, null, reload);
}
