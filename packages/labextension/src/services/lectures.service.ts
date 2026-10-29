// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Lecture } from '../model/lecture';
import { request } from './request.service';
import { User } from '../model/user';
import { HTTPMethod } from './enums/http-methods.enum';
import { LectureListDto } from '../model/lectureListDto';

const baseUrl = '/api/lectures';

export function getLectures(
  filters: { [key: string]: boolean | string | number | null },
  instructor: boolean = false,
  page: number = 1,
  perPage: number = 20,
  reload = false
): Promise<LectureListDto> {
  let url = baseUrl;
  const params = new URLSearchParams();

  for (const key in filters) {
    if (filters[key] !== null) {
      params.append(key, String(filters[key]));
    }
  }
  params.append('instructor', String(instructor));
  params.append('page', String(page));
  params.append('per_page', String(perPage));
  url += '?' + params.toString();
  return request<LectureListDto>(HTTPMethod.GET, url, null, reload);
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
