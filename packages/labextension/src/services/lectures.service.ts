// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Lecture } from '../model/lecture';
import { request } from './request.service';
import { User } from '../model/user';
import { HTTPMethod } from './enums/http-methods.enum';

const baseUrl = '/api/lectures';

export function getLectures(
  filters: { [key: string]: boolean },
  reload = false
): Promise<Lecture[]> {
  let url = baseUrl;
  const params = new URLSearchParams();

  for (const key in filters) {
    if (filters[key] !== null) {
      params.append(key, String(filters[key]));
    }
  }
  url += '?' + params.toString();
  return request<Lecture[]>(HTTPMethod.GET, url, null, reload);
}

export function getLecture(
  lectureId: number,
  reload = false
): Promise<Lecture> {
  return request<Lecture>(
    HTTPMethod.GET,
    `${baseUrl}/${lectureId}`,
    null,
    reload
  );
}

export function updateLecture(lecture: Lecture): Promise<Lecture> {
  return request<Lecture, Lecture>(
    HTTPMethod.PUT,
    `${baseUrl}/${lecture.id}`,
    lecture
  );
}

export function deleteLecture(lectureId: number): Promise<void> {
  return request<void>(HTTPMethod.DELETE, `${baseUrl}/${lectureId}`, null);
}

export function getLectureUsers(
  lectureId: number,
  reload: boolean = false
): Promise<{ instructors: User[]; tutors: User[]; students: User[] }> {
  return request<{
    instructors: User[];
    tutors: User[];
    students: User[];
  }>(HTTPMethod.GET, `${baseUrl}/${lectureId}/users`, null, reload);
}
