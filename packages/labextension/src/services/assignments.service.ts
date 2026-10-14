// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../model/assignment';
import { AssignmentDetail } from '../model/assignmentDetail';
import { request } from './request.service';
import { HTTPMethod } from './enums/http-methods.enum';

export const baseUrl = (lectureId: number) => {
  return `/api/lectures/${lectureId}/assignments`;
};

export function getAllAssignments(
  lectureId: number,
  reload = false,
  includeSubmissions = false
): Promise<AssignmentDetail[]> {
  let url = baseUrl(lectureId);
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
    `${baseUrl(lectureId)}/${assignmentId}`,
    null,
    reload
  );
}

export function createAssignment(
  lectureId: number,
  assignment: Assignment
): Promise<Assignment> {
  return request<Assignment, Assignment>(
    HTTPMethod.POST,
    baseUrl(lectureId),
    assignment
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
  let url = `${baseUrl(lectureId)}/${assignment.id}`;
  url += '?' + searchParams;

  return request<Assignment, Assignment>(HTTPMethod.PUT, url, assignment);
}

export function getAssignmentProperties(
  lectureId: number,
  assignmentId: number,
  reload: boolean = false
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `${baseUrl(lectureId)}/${assignmentId}/properties`,
    null,
    reload
  );
}

export function generateAssignment(
  lectureId: number,
  assignment: Assignment
): Promise<any> {
  return request<any>(
    HTTPMethod.PUT,
    `${baseUrl(lectureId)}/${assignment.id}/generate`,
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
  let url = `${baseUrl(lectureId)}/${assignmentId}`;
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
    `${baseUrl(lectureId)}/${assignmentId}`,
    null
  );
}

export function getConfig(): Promise<any> {
  return request<any>(HTTPMethod.GET, '/api/config', null);
}
