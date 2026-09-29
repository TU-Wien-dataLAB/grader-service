// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../model/assignment';
import { request } from './request.service';
import { Submission } from '../model/submission';
import { baseUrl } from './file.service';
import { HTTPMethod } from './enums/http-methods.enum';
import { RepoType } from '../app/components/utils/repo-type';

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
