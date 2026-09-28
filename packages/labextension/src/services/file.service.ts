import { Lecture } from '../model/lecture';
import { Assignment } from '../model/assignment';
import { RepoType } from '../app/components/utils/repo-type';
import { request } from './request.service';
import { HTTPMethod } from './enums/http-methods.enum';
import { RemoteFileStatus } from '../model/remoteFileStatus';

export const baseUrl = (props: { lectureId: number; assignmentId: number }) => {
  return `/api/lectures/${props.lectureId}/assignments/${props.assignmentId}/`;
};

interface IGitLogObject {
  commit: string;
  author: string;
  date: string;
  ref: string;
  commit_msg: string;
  pre_commit: string;
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
