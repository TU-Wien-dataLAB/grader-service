// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../model/assignment';
import { Lecture } from '../model/lecture';
import { Submission } from '../model/submission';
import { request, HTTPMethod } from './request.service';

export function submitAssignment(
  lecture: Lecture,
  assignment: Assignment,
  submit = false
) {
  let url = `/lectures/${lecture.id}/assignments/${assignment.id}/push/assignment`;
  if (submit) {
    const searchParams = new URLSearchParams({
      submit: String(submit)
    });
    url += '?' + searchParams;
  }
  return request<void>(HTTPMethod.PUT, url);
}

export async function pullFeedback(
  lecture: Lecture,
  assignment: Assignment,
  submission: Submission
) {
  return request<void>(
    HTTPMethod.GET,
    `/lectures/${lecture.id}/assignments/${assignment.id}/grading/${submission.id}/pull/feedback`
  );
}

export function getSubmissions(
  lecture: Lecture,
  assignment: Assignment,
  filter = 'none'
): Promise<Submission[]> {
  let url = `/lectures/${lecture.id}/assignments/${assignment.id}/submissions`;
  if (filter) {
    const searchParams = new URLSearchParams({
      filter: filter
    });
    url += '?' + searchParams;
  }
  return request<any>(HTTPMethod.GET, url);
}

export function getAllSubmissions(
  lecture: Lecture,
  assignment: Assignment,
  filter: 'none' | 'latest' | 'best' = 'none',
  instructor = true
): Promise<Submission[]> {
  let url = `/lectures/${lecture.id}/assignments/${assignment.id}/submissions`;

  if (filter || instructor) {
    const searchParams = new URLSearchParams({
      'instructor-version': String(instructor),
      filter: filter
    });
    url += '?' + searchParams;
  }
  return request<Submission[]>(HTTPMethod.GET, url);
}

export function getFeedback(
  lecture: Lecture,
  assignment: Assignment,
  latest = false,
  instructor = false
): Promise<any> {
  let url = `/lectures/${lecture.id}/assignments/${assignment.id}/feedback`;
  if (latest || instructor) {
    const searchParams = new URLSearchParams({
      'instructor-version': String(instructor),
      latest: String(latest)
    });
    url += '?' + searchParams;
  }
  return request<any>(HTTPMethod.GET, url);
}

export function getProperties(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<object> {
  const url = `/lectures/${lectureId}/assignments/${assignmentId}/submissions/${submissionId}/properties`;
  return request<object>(HTTPMethod.GET, url);
}

export function updateProperties(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  properties: any
): Promise<Submission> {
  const url = `/lectures/${lectureId}/assignments/${assignmentId}/submissions/${submissionId}/properties`;
  return request<Submission>(HTTPMethod.PUT, url, properties);
}

export function getSubmission(
  lectureId: number,
  assignmentId: number,
  submissionId: number
): Promise<Submission> {
  const url = `/lectures/${lectureId}/assignments/${assignmentId}/submissions/${submissionId}`;
  return request<Submission>(HTTPMethod.GET, url);
}

export function updateSubmission(
  lectureId: number,
  assignmentId: number,
  submissionId: number,
  sub: Submission
): Promise<Submission> {
  const url = `/lectures/${lectureId}/assignments/${assignmentId}/submissions/${submissionId}`;
  return request<Submission>(HTTPMethod.PUT, url, sub);
}
