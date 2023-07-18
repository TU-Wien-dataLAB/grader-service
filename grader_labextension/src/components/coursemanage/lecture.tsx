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
  LinearProgress, Stack, TableCell, TableRow,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import {
  createAssignment, deleteAssignment,
  getAllAssignments
} from '../../services/assignments.service';
import { AssignmentComponent } from './assignment';
import { AgreeDialog, CreateDialog, EditLectureDialog } from '../util/dialog';
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
import { useNavigate, useNavigation, useRouteLoaderData } from 'react-router-dom';
import { ButtonTr, GraderTable } from '../util/table';
import { DeadlineComponent } from '../util/deadline';


interface IAssignmentTableProps {
  lecture: Lecture;
  rows: Assignment[];
}

const AssignmentTable = (props: IAssignmentTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'Name' },
    { name: 'Points', width: 75 },
    { name: 'Deadline' },
    { name: 'Status' },
    { name: 'Show Details' },
    { name: 'Delete Assignment', width: 150 }
  ];

  const [showDialog, setShowDialog] = React.useState(false);
  const [deleteFunction, setDeleteFunction] = React.useState({handleAgree: null as () => void});

  const getDeleteAssignmentFunction = (assignmentId: number) => {
    return async () => {
      try {
        await deleteAssignment(
          props.lecture.id,
          assignmentId
        );
        enqueueSnackbar('Successfully Deleted Assignment', {
          variant: 'success'
        });
      } catch (error: any) {
        enqueueSnackbar(error.message, {
          variant: 'error'
        });
      }
      setShowDialog(false);
    };
  };

  return (
    <>
      <GraderTable<Assignment>
        headers={headers}
        rows={props.rows}
        rowFunc={row => {
          return (
            <TableRow
              key={row.name}
              component={ButtonTr}
              onClick={() => navigate(`/lecture/${props.lecture.id}/assignment/${row.id}`)}
            >
              <TableCell component='th' scope='row'>
                <Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>{row.name}</Typography>
              </TableCell>
              <TableCell style={{ width: 75 }}>{row.points}</TableCell>
              <TableCell><DeadlineComponent component={'chip'} due_date={row.due_date} compact={true} /></TableCell>
              <TableCell>{row.status}</TableCell>
              <TableCell>
                <Button variant='contained' size={'small'}>Details</Button>
              </TableCell>
              <TableCell style={{ width: 150 }}>
                <Button
                  size={'small'}
                  color='error'
                  variant='contained'
                  onClick={(e) => {
                    setDeleteFunction({handleAgree: getDeleteAssignmentFunction(row.id)});
                    setShowDialog(true);
                    e.stopPropagation();
                  }}
                >
                  Delete
                </Button>
              </TableCell>
            </TableRow>
          );
        }}
      />
      <AgreeDialog open={showDialog} title={'Delete Assignment'} message={'Do you wish to delete this assignment?'}
                   handleDisagree={() => setShowDialog(false)} {...deleteFunction} />
    </>

  );
};


interface ILectureComponentProps {
  root: HTMLElement;
}

export const LectureComponent = (props: ILectureComponentProps) => {
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: { instructors: string[], tutors: string[], students: string[] }
  };
  const navigation = useNavigation();

  const [lectureState, setLecture] = React.useState(lecture);
  const [assignmentsState, setAssignments] = React.useState(assignments);

  const onAssignmentDelete = () => {
    getAllAssignments(lectureState.id).then(response => {
      setAssignments(response);
    });
    deleteKey('cm-opened-assignment');
  };

  if (navigation.state === 'loading') {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }

  return (
    <Stack direction={'column'} sx={{ m: 5 }}>
      <Typography variant={'h5'} sx={{ mr: 2 }}>
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
      <Stack direction={'row'} justifyContent={'flex-end'} alignItems={'center'} spacing={2} sx={{ mb: 1 }}>
        <CreateDialog
          lecture={lectureState}
          handleSubmit={assigment => {
            setAssignments((oldAssignments: Assignment[]) => [
              ...oldAssignments,
              assigment
            ]);
          }}
        />
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
      </Stack>

      <Stack><Typography variant={'h6'}>Assignments</Typography></Stack>
      <AssignmentTable lecture={lectureState} rows={assignmentsState} />
    </Stack>
  );
};
