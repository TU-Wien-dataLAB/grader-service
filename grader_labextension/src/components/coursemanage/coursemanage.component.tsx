// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { getAllLectures } from '../../services/lectures.service';
import { Scope, UserPermissions } from '../../services/permission.service';
import { LectureComponent } from './lecture';
import { enqueueSnackbar } from 'notistack';

export interface ICourseManageProps {
  // lectures: Array<Lecture>;
  root: HTMLElement;
}

export const CourseManageComponent = (props: ICourseManageProps) => {
  const [lectures, setLectures] = React.useState([] as Lecture[]);
  const [completedLectures, setCompletedLectures] = React.useState(
    [] as Lecture[]
  );
  React.useEffect(() => {
    UserPermissions.loadPermissions().then(
      () => {
        getAllLectures().then(l => setLectures(l));
        getAllLectures(true).then(l => setCompletedLectures(l));
      },
      error =>
        enqueueSnackbar(error.message, {
          variant: 'error'
        })
    );
  }, [props]);

  return (
    <div className="course-list">
      <h1>
        <p className="course-header">Course Management</p>
      </h1>
      {lectures
        .filter(el => UserPermissions.getScope(el) > Scope.student)
        .map((el, index) => (
          <LectureComponent lecture={el} root={props.root} expanded={true} />
        ))}
      {completedLectures
        .filter(el => UserPermissions.getScope(el) > Scope.student)
        .map((el, index) => (
          <LectureComponent lecture={el} root={props.root} expanded={false} />
        ))}
    </div>
  );
};
