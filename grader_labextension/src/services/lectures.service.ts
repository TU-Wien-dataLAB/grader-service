// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Lecture } from '../model/lecture';
import { request, HTTPMethod } from './request.service';

export function createLecture(lecture: Lecture): Promise<Lecture> {
  return request<Lecture>(HTTPMethod.POST, '/lectures', lecture);
}

export function getAllLectures(complete: boolean = false, reload = false): Promise<Lecture[]> {
  let url = '/lectures'
  if (complete) {
      let searchParams = new URLSearchParams({
        "complete": String(complete)
      })
      url += '?' + searchParams;
    }
  return request<Lecture[]>(HTTPMethod.GET, url, reload);
}

export function updateLecture(lecture: Lecture): Promise<Lecture> {
  return request<Lecture, Lecture>(HTTPMethod.PUT, `/lectures/${lecture.id}`, lecture);
}

export function getLecture(lectureId: number, reload = false): Promise<Lecture> {
  return request<Lecture>(HTTPMethod.GET, `/lectures/${lectureId}`, reload);
}

export function deleteLecture(lectureId: number): void {
  request<void>(HTTPMethod.DELETE, `/lectures/${lectureId}`);
}

//TODO: create Datapackage model to replace any
export function getUsers(lecture: Lecture) : Promise<any> {
  return request<any>(HTTPMethod.GET, `/lectures/${lecture.id}/users`);
}
