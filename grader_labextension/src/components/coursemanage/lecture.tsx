// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Button,
  Card,
  CardActions,
  CardContent,
  Collapse,
  Grid,
  LinearProgress,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import {
  createAssignment,
  getAllAssignments
} from '../../services/assignments.service';
import { AssignmentComponent } from './assignment';
import { CreateDialog, EditLectureDialog } from '../util/dialog';
import {
  getLecture,
  getUsers,
  updateLecture
} from '../../services/lectures.service';
import { red } from '@mui/material/colors';
import { enqueueSnackbar } from 'notistack';
import {
  deleteKey,
  loadBoolean,
  storeBoolean
} from '../../services/storage.service';
import { useRouteLoaderData } from 'react-router-dom';


interface ILectureComponentProps {
  root: HTMLElement;
}

export const LectureComponent = (props: ILectureComponentProps) => {
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: {instructors: string[], tutors: string[], students: string[]}
  };

  const [lectureState, setLecture] = React.useState(lecture);
  const [assignmentsState, setAssignments] = React.useState(assignments);

  const onAssignmentDelete = () => {
    getAllAssignments(lectureState.id).then(response => {
      setAssignments(response);
    });
    deleteKey('cm-opened-assignment');
  };

  if (assignmentsState === null) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }
  return (
    <div>
      <Card
        sx={{ backgroundColor: 'background.paper' }}
        className='lecture-card'
      >
        <CardContent sx={{ mb: -1, display: 'flex' }}>
          <Typography variant={'h5'} sx={{ mr: 2 }}>
            <Typography
              color={'text.secondary'}
              sx={{
                display: 'inline-block',
                mr: 0.75,
                fontSize: 16
              }}
            >
              Lecture:
            </Typography>
            {lectureState.name}
            {lectureState.complete ? (
              <Typography
                sx={{
                  display: 'inline-block',
                  ml: 0.75,
                  fontSize: 16,
                  color: red[400]
                }}
              >
                complete
              </Typography>
            ) : null}
          </Typography>
          <EditLectureDialog
            lecture={lectureState}
            handleSubmit={updatedLecture => {
              updateLecture(updatedLecture).then(
                response => {
                  setLecture(response);
                },
                error => {
                  enqueueSnackbar(error.message, {
                    variant: 'error'
                  });
                }
              );
            }}
          />
        </CardContent>

        <CardContent>
          <Grid container spacing={2} alignItems='stretch'>
            {assignmentsState.map((el: Assignment) => (
              <Grid
                item
                gridAutoColumns={'1fr'}
                sx={{
                  maxWidth: 225,
                  minWidth: 225,
                  minHeight: '100%',
                  m: 1.5
                }}
              >
                <AssignmentComponent
                  lecture={lectureState}
                  assignment={el}
                  root={props.root}
                  users={users}
                  onDeleted={onAssignmentDelete}
                />
              </Grid>
            ))}
            <Grid
              item
              gridAutoColumns={'1fr'}
              sx={{
                maxWidth: 225,
                minWidth: 225,
                minHeight: 225,
                heigth: '100%',
                m: 1.5
              }}
            >
              <CreateDialog
                lecture={lectureState}
                handleSubmit={assigment => {
                  setAssignments((oldAssignments: Assignment[]) => [
                    ...oldAssignments,
                    assigment
                  ]);
                }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </div>
  );
};
