import { RepoType } from '../app/components/utils/repo-type';
import { HTTPMethod, request } from './request.service';
import { Lecture } from '../model/lecture';
import { Assignment } from '../model/assignment';
import { buildBaseUrl } from './assignments.service';

export function pushAssignment(
  lectureId: number,
  assignmentId: number,
  repoType: RepoType,
  commitMessage?: string,
  selectedFiles?: string[]
): Promise<void> {
  let url = `${buildBaseUrl(lectureId)}/${assignmentId}/push/${repoType}`;
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
    `${buildBaseUrl(lectureId)}/${assignmentId}/pull/${repoType}`,
    null
  );
}

export function resetAssignment(
  lecture: Lecture,
  assignment: Assignment
): Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `${buildBaseUrl(lecture.id)}/${assignment.id}/reset`,
    null
  );
}
