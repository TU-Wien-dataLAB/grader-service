// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../model/assignment';
import { AssignmentDetail } from '../model/assignmentDetail';
import { Lecture } from '../model/lecture';
import { HTTPMethod, request } from './request.service';
import { RepoType } from '../components/util/repo-type';

export function createAssignment(
  lectureId: number,
  assignment: Assignment
): Promise<Assignment> {
  return request<Assignment, Assignment>(
    HTTPMethod.POST,
    `/api/lectures/${lectureId}/assignments`,
    assignment
  );
}

export function getAllAssignments(
  lectureId: number,
  reload = false,
  includeSubmissions = false
): Promise<AssignmentDetail[]> {
  let url = `/api/lectures/${lectureId}/assignments`;
  if (includeSubmissions) {
    const searchParams = new URLSearchParams({
      'include-submissions': String(includeSubmissions)
    });
    url += '?' + searchParams;
  }
  return request<AssignmentDetail[]>(HTTPMethod.GET, url, null, reload);
}

export function getAssignment(
  lectureId: number,
  assignmentId: number,
  reload = false
): Promise<Assignment> {
  return request<Assignment>(
    HTTPMethod.GET,
    `/api/lectures/${lectureId}/assignments/${assignmentId}`,
    null,
    reload
  );
}

export function getAssignmentProperties(
  lectureId: number,
  assignmentId: number,
  reload: boolean = false
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `/api/lectures/${lectureId}/assignments/${assignmentId}/properties`,
    null,
    reload
  );
}

export function updateAssignment(
  lectureId: number,
  assignment: Assignment,
  recalcScores: boolean = false
): Promise<Assignment> {
  const searchParams = new URLSearchParams({
    'recalc-scores': String(recalcScores)
  });
  let url = `/api/lectures/${lectureId}/assignments/${assignment.id}`;
  url += '?' + searchParams;

  return request<Assignment, Assignment>(HTTPMethod.PUT, url, assignment);
}

export function generateAssignment(
  lectureId: number,
  assignment: Assignment
): Promise<any> {
  return request<any>(
    HTTPMethod.PUT,
    `/api/lectures/${lectureId}/assignments/${assignment.id}/generate`,
    null
  );
}

export function fetchAssignment(
  lectureId: number,
  assignmentId: number,
  instructor: boolean = false,
  metadataOnly: boolean = false,
  reload: boolean = false
): Promise<Assignment> {
  let url = `/api/lectures/${lectureId}/assignments/${assignmentId}`;
  if (instructor || metadataOnly) {
    const searchParams = new URLSearchParams({
      'instructor-version': String(instructor),
      'metadata-only': String(metadataOnly)
    });
    url += '?' + searchParams;
  }

  return request<Assignment>(HTTPMethod.GET, url, null, reload);
}

export function deleteAssignment(
  lectureId: number,
  assignmentId: number
): Promise<void> {
  return request<void>(
    HTTPMethod.DELETE,
    `/api/lectures/${lectureId}/assignments/${assignmentId}`,
    null
  );
}

export function pushAssignment(
  lectureId: number,
  assignmentId: number,
  repoType: RepoType,
  commitMessage?: string,
  selectedFiles?: string[]
): Promise<void> {
  let url = `/api/lectures/${lectureId}/assignments/${assignmentId}/push/${repoType}`;
  if (commitMessage && commitMessage !== undefined) {
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
    `/api/lectures/${lectureId}/assignments/${assignmentId}/pull/${repoType}`,
    null
  );
}

export function resetAssignment(
  lecture: Lecture,
  assignment: Assignment
): Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `/api/lectures/${lecture.id}/assignments/${assignment.id}/reset`,
    null
  );
}

export function getConfig(): Promise<any> {
  return request<any>(HTTPMethod.GET, '/api/config', null);
}
