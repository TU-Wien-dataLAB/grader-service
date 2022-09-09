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

interface ILectureComponentProps {
  lecture: Lecture;
  root: HTMLElement;
  expanded?: boolean;
}

export const LectureComponent = (props: ILectureComponentProps) => {
  const [lecture, setLecture] = React.useState(props.lecture);
  const [assignments, setAssignments] = React.useState([]);
  const [expanded, setExpanded] = React.useState(
    loadBoolean('cm-expanded', lecture) !== null
      ? loadBoolean('cm-expanded', lecture)
      : props.expanded === undefined
      ? false
      : props.expanded
  );
  const [users, setUsers] = React.useState(null);

  React.useEffect(() => {
    getAllAssignments(lecture.id).then(response => {
      setAssignments(response);
    });

    getUsers(lecture).then(response => {
      setUsers(response);
    });
  }, [lecture]);

  const onAssignmentDelete = () => {
    getAllAssignments(lecture.id).then(response => {
      setAssignments(response);
    });
    deleteKey('cm-opened-assignment');
  };

  const handleExpandClick = () => {
    storeBoolean('cm-expanded', !expanded, lecture);
    setExpanded(!expanded);
  };
  if (assignments === null) {
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
        sx={{ backgroundColor: expanded ? '#fafafa' : 'background.paper' }}
        elevation={expanded ? 0 : 2}
        className="lecture-card"
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
            {lecture.name}
            {lecture.complete ? (
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
            lecture={lecture}
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

        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <CardContent>
            <Grid container spacing={2} alignItems="stretch">
              {assignments.map((el: Assignment) => (
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
                    lecture={lecture}
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
                  lecture={lecture}
                  handleSubmit={assigment => {
                    setAssignments((oldAssignments: Assignment[]) => [
                      ...oldAssignments,
                      assigment
                    ]);
                    setExpanded(true);
                  }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Collapse>
        <CardActions>
          <Button size="small" sx={{ ml: 'auto' }} onClick={handleExpandClick}>
            {(expanded ? 'Hide' : 'Show') + ' Assignments'}
          </Button>
        </CardActions>
      </Card>
    </div>
  );
};
