import { RepoType } from '../app/components/utils/repo-type';
import { request } from './request.service';
import { baseUrl } from './file.service';
import { HTTPMethod } from './enums/http-methods.enum';

export function pushAssignment(
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
