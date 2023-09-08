// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {
  Button, IconButton,
  Card,
  CardActions,
  CardContent,
  Collapse,
  Grid,
  LinearProgress, Stack, TableCell, TableRow,
  Typography,
  Box
} from '@mui/material';
import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import {
  createAssignment, deleteAssignment,
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
import { useNavigate, useNavigation, useRouteLoaderData } from 'react-router-dom';
import { ButtonTr, GraderTable } from '../util/table';
import { DeadlineComponent } from '../util/deadline';
import DoneIcon from '@mui/icons-material/Done';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import { showDialog } from '../util/dialog-provider';
import { useEffect } from 'react';
import { Submission } from '../../model/submission';


interface IAssignmentTableProps {
  lecture: Lecture;
  rows: Assignment[];
  setAssignments: React.Dispatch<React.SetStateAction<Assignment[]>>,
}

const AssignmentTable = (props: IAssignmentTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'Name' },
    { name: 'Points', width: 100 },
    { name: 'Deadline', width: 200 },
    { name: 'Status', width: 130 },
    { name: 'Show Details', width: 75 },
    { name: 'Delete Assignment', width: 100 }
  ];

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
              <TableCell>{row.points}</TableCell>
              <TableCell><DeadlineComponent component={'chip'} due_date={row.due_date} compact={true} /></TableCell>
              <TableCell>{row.status}</TableCell>
              <TableCell>
                <IconButton aria-label='detail view' size={'small'}>
                  <SearchIcon />
                </IconButton>
              </TableCell>
              <TableCell>
                <IconButton
                  aria-label='delete assignment'
                  size={'small'}
                  onClick={(e) => {
                    showDialog(
                      'Delete Assignment',
                      'Do you wish to delete this assignment?',
                      async () => {
                        try {
                          await deleteAssignment(
                            props.lecture.id,
                            row.id
                          );
                          enqueueSnackbar('Successfully Deleted Assignment', {
                            variant: 'success'
                          });
                          props.setAssignments(props.rows.filter(a => a.id !== row.id));
                        } catch (error: any) {
                          enqueueSnackbar(error.message, {
                            variant: 'error'
                          });
                        }
                      });
                    e.stopPropagation();
                  }}
                >
                  <CloseIcon sx={{ color: red[500] }} />
                </IconButton>
              </TableCell>
            </TableRow>
          );
        }}
      />
    </>

  );
};


export const LectureComponent = () => {
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: { instructors: string[], tutors: string[], students: string[] }
  };
  const navigation = useNavigation();

  const [lectureState, setLecture] = React.useState(lecture);
  const [assignmentsState, setAssignments] = React.useState(assignments);

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
    <Stack direction={'column'} sx={{ m: 5, flex: 1 }}>
      <Typography variant={'h4'} sx={{ mr: 2 }}>
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
      <AssignmentTable lecture={lectureState} rows={assignmentsState} setAssignments={setAssignments} />
    </Stack>
  );
};
