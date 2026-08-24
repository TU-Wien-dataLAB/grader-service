// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../model/assignment';
import { User } from '../model/user';
import { request } from './request.service';
import { Submission } from '../model/submission';
import { baseUrl } from './file.service';
import { HTTPMethod } from './enums/http-methods.enum';

export function autogradeSubmission(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<any> {
  return request<Assignment>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}grading/${submissionId}/auto`,
    null
  );
}

export function generateFeedback(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<Submission> {
  return request<Submission>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}grading/${submissionId}/feedback`,
    null
  );
}

export function getGrade(
  lectureId: number,
  assignmentId: number,
  student: User
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}grading/${student.name}/score`,
    null
  );
}

export function getStudentSubmissions(
  username: string,
  format: 'json' | 'csv' = 'csv',
  reload = false
): Promise<any> {
  let url = `/api/users/${username}/submissions`;
  const params = new URLSearchParams({
    format: format
  });
  url += '?' + params.toString();
  return request<any>(HTTPMethod.GET, url, null, reload);
}

export function getManualFeedback(
  lectureId: number,
  assignmentId: number,
  student: User
): Promise<object> {
  return request<object>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}grading/${student.name}/manual`,
    null
  );
}

export function createManualFeedback(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<any> {
  return request<any>(
    HTTPMethod.GET,
    `${baseUrl({ lectureId, assignmentId })}grading/${submissionId}/manual`,
    null
  );
}

export function updateManualFeedback(
  lectureId: number,
  assignmentId: number,
  student: User,
  manual: any
): Promise<any> {
  return request<any>(
    HTTPMethod.PUT,
    `${baseUrl({ lectureId, assignmentId })}grading/${student.name}/manual`,
    manual
  );
}

export function deleteManualFeedback(
  lectureId: number,
  assignmentId: number,
  student: User,
  manual: any
): Promise<any> {
  return request<any>(
    HTTPMethod.DELETE,
    `${baseUrl({ lectureId, assignmentId })}grading/${student.name}/manual`,
    manual
  );
}
