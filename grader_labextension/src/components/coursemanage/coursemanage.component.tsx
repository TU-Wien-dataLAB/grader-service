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
import { useRouteLoaderData, Link as RouterLink } from 'react-router-dom';
import { ListItem, ListItemProps, ListItemText } from '@mui/material';

export interface ICourseManageProps {
  // lectures: Array<Lecture>;
  root: HTMLElement;
}

interface ListItemLinkProps extends ListItemProps {
  to: string;
  text: string;
}

const ListItemLink = (props: ListItemLinkProps) => {
  const { to, ...other } = props;
  return (
    <li>
      <ListItem component={RouterLink as any} to={to} {...other}>
        <ListItemText primary={props.text} />
      </ListItem>
    </li>
  );
}


export const CourseManageComponent = (props: ICourseManageProps) => {
  const allLectures = useRouteLoaderData("root") as {lectures: Lecture[], completedLectures: Lecture[]};

  return (
    <div className="course-list">
      <h1>
        <p className="course-header">Course Management</p>
      </h1>
      {allLectures.lectures
        .filter(el => UserPermissions.getScope(el) > Scope.student)
        .map((el, index) => (
          <ListItemLink to={`/lecture/${el.id}`} text={el.name} />
        ))}
      {allLectures.completedLectures
        .filter(el => UserPermissions.getScope(el) > Scope.student)
        .map((el, index) => (
          <ListItemLink to={`/lecture/${el.id}`} text={el.name} />
        ))}
    </div>
  );
};
