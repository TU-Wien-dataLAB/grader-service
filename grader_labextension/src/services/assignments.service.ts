// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {Assignment} from '../model/assignment';
import {Lecture} from '../model/lecture';
import {request, HTTPMethod} from './request.service'

export function createAssignment(lectureId: number, assignment: Assignment): Promise<Assignment> {
  return request<Assignment, Assignment>(HTTPMethod.POST, `/lectures/${lectureId}/assignments`, assignment)
}

export function getAllAssignments(lectureId: number, reload = false): Promise<Assignment[]> {
  return request<Assignment[]>(HTTPMethod.GET, `/lectures/${lectureId}/assignments`, reload)
}

export function getAssignment(lectureId: number, assignmentId: number, reload = false): Promise<Assignment> {
  return request<Assignment>(HTTPMethod.GET, `/lectures/${lectureId}/assignments/${assignmentId}`, reload)
}

export function getAssignmentProperties(lectureId: number, assignmentId: number): Promise<any> {
  return request<any>(HTTPMethod.GET, `/lectures/${lectureId}/assignments/${assignmentId}/properties`)
}

export function updateAssignment(lectureId: number, assignment: Assignment): Promise<Assignment> {
  return request<Assignment, Assignment>(HTTPMethod.PUT, `/lectures/${lectureId}/assignments/${assignment.id}`, assignment)
}

export function generateAssignment(lectureId: number, assignment: Assignment): Promise<any> {
  return request<any>(HTTPMethod.PUT, `/lectures/${lectureId}/assignments/${assignment.id}/generate`)
}

export function fetchAssignment(lectureId: number, assignmentId: number, instructor: boolean = false, metadataOnly: boolean = false): Promise<Assignment> {
  let url = `/lectures/${lectureId}/assignments/${assignmentId}`;
  if (instructor || metadataOnly) {
    let searchParams = new URLSearchParams({
      "instructor-version": String(instructor),
      "metadata-only": String(metadataOnly)
    })
    url += '?' + searchParams;
  }

  return request<Assignment>(HTTPMethod.GET, url);
}

export function deleteAssignment(lectureId: number, assignmentId: number): Promise<void> {
  return request<void>(
    HTTPMethod.DELETE,
    `/lectures/${lectureId}/assignments/${assignmentId}`
  );
}

export function pushAssignment(lectureId: number, assignmentId: number, repoType: string, commitMessage?: string): Promise<void> {
  let url = `/lectures/${lectureId}/assignments/${assignmentId}/push/${repoType}`;
  if (commitMessage) {
    let searchParams = new URLSearchParams({
      'commit-message': commitMessage
    })
    url += '?' + searchParams;
  }
  return request<void>(HTTPMethod.PUT, url);
}

export function pullAssignment(lectureId: number, assignmentId: number, repoType: string): Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `/lectures/${lectureId}/assignments/${assignmentId}/pull/${repoType}`
  );
}

export function resetAssignment(lecture: Lecture, assignment: Assignment) : Promise<void> {
  return request<void>(
    HTTPMethod.GET,
    `/lectures/${lecture.id}/assignments/${assignment.id}/reset`
  );
}

