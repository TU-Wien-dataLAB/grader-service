// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { getAllLectures } from '../../services/lectures.service';
import { Lecture } from '../../model/lecture';
import { LectureComponent } from './lecture';
//import { AlertProps, Alert, Portal, AlertTitle } from '@mui/material';

import { useRouteLoaderData, Link as RouterLink } from 'react-router-dom';
import { ListItem, ListItemProps, ListItemText } from '@mui/material';
/**
 * Props for LectureListComponent.
 */
export interface ILectureListProps {
  root: HTMLElement;
}

interface ListItemLinkProps extends ListItemProps {
    to: string;
    text: string;
}

const ListItemLink = (props: ListItemLinkProps) => { 
    const { to, ...other } = props;
    return (
        <li>
            <ListItem component={RouterLink as any } to={to} {...other}>
                <ListItemText primary={props.text} />
            </ListItem>
        </li>
    );
};

/**
 * Renders the lectures which the student addends.
 * @param props Props of the lecture file components
 */
export const AssignmentManageComponent = (props: ILectureListProps): JSX.Element => {
  const allLectures = useRouteLoaderData("root") as { lectures: Lecture[], completedLectures: Lecture[] };

  return (
    <div className="course-list">
      <h1>
        <p className="course-header">Assignment Management</p>
      </h1>
      {/* {lectures.map((el, index) => (
        <LectureComponent lecture={el} root={props.root} open={true} />
      ))}
      {lectures.length === 0 ? (
        <Alert sx={{ m: 3 }} severity="info">
          No active lectures found
        </Alert>
      ) : null} */}

      {allLectures.lectures
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((el, index) => (
          <ListItemLink key={index} to={`/lecture/${el.id}`} text={el.name} />
        ))}
    </div>
  );
};
