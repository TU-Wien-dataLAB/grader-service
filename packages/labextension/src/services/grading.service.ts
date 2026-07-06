// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Lecture } from '../model/lecture';
import { Assignment } from '../model/assignment';
import { User } from '../model/user';
import { request, HTTPMethod } from './request.service';
import { Submission } from '../model/submission';

export function createManualFeedback(
  lectid: number,
  assignid: number,
  subid: number
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `/api/lectures/${lectid}/assignments/${assignid}/grading/${subid}/manual`,
    null
  );
}

export function saveSubmissions(
  lecture: Lecture,
  assignment: Assignment,
  filter: 'none' | 'latest' | 'best' = 'none'
): Promise<any> {
  let url = `/api/lectures/${lecture.id}/assignments/${assignment.id}/submissions/save`;
  if (filter) {
    const searchParams = new URLSearchParams({
      filter: filter
    });
    url += '?' + searchParams;
  }
  return request<any>(HTTPMethod.PUT, url, null);
}

export function autogradeSubmission(
  lecture: Lecture,
  assignment: Assignment,
  submission: Submission
): Promise<any> {
  return request<Assignment>(
    HTTPMethod.GET,
    `/api/lectures/${lecture.id}/assignments/${assignment.id}/grading/${submission.id}/auto`,
    null
  );
}

export function generateFeedback(
  lecture: Lecture,
  assignment: Assignment,
  submission: Submission
): Promise<Submission> {
  return request<Submission>(
    HTTPMethod.GET,
    `/api/lectures/${lecture.id}/assignments/${assignment.id}/grading/${submission.id}/feedback`,
    null
  );
}

//response is not a schema => any
//TODO: should prob be changed
export function getStudentSubmissions(
  lecture: Lecture,
  assignment: Assignment,
  reload = false
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `/api/lectures/${lecture.id}/assignements/${assignment.id}/grading`,
    null,
    reload
  );
}

export function getManualFeedback(
  lecture: Lecture,
  assignment: Assignment,
  student: User
): Promise<object> {
  return request<object>(
    HTTPMethod.GET,
    `/api/lectures/${lecture.id}/assignments/${assignment.id}/grading/${student.name}/manual`,
    null
  );
}

export function updateManualFeedback(
  lecture: Lecture,
  assignment: Assignment,
  student: User,
  manual: any
): Promise<any> {
  return request<any>(
    HTTPMethod.PUT,
    `/api/lectures/${lecture.id}/assignements/${assignment.id}/grading/${student.name}/manual`,
    manual
  );
}

export function deleteManualFeedback(
  lecture: Lecture,
  assignment: Assignment,
  student: User,
  manual: any
): Promise<any> {
  return request<any>(
    HTTPMethod.DELETE,
    `/api/lectures/${lecture.id}/assignments/${assignment.id}/grading/${student.name}/manual`,
    manual
  );
}

export function getGrade(
  lecture: Lecture,
  assignment: Assignment,
  student: User
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `/api/lectures/${lecture.id}/assignments/${assignment.id}/grading/${student.name}/score`,
    null
  );
}
