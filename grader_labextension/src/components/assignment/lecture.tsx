// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.
import * as React from 'react';
import moment from 'moment';
import { useNavigate, useNavigation, useRouteLoaderData } from 'react-router-dom';
import {
  Button, IconButton,
  Card,
  LinearProgress, Stack, TableCell, TableRow,
  Typography, Box
} from '@mui/material';
import { red, blue, green, grey } from '@mui/material/colors';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined';
import DoneIcon from '@mui/icons-material/Done';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { enqueueSnackbar } from 'notistack';

import { ButtonTr, GraderTable, headerWidth, IHeaderCell } from '../util/table';
import { DeadlineComponent, getDisplayDate } from '../util/deadline';
import { Assignment } from '../../model/assignment';
import { AssignmentDetail } from '../../model/assignmentDetail';
import { Submission } from '../../model/submission';
import { Lecture } from '../../model/lecture';
import { pullAssignment, pushAssignment, resetAssignment } from '../../services/assignments.service';
import { showDialog } from '../util/dialog-provider';
import EditOffIcon from '@mui/icons-material/EditOff';
import { getFiles, lectureBasePath } from '../../services/file.service';
import { openBrowser } from '../coursemanage/overview/util';

/*
    * Buttons for AssignmentTable
    * */
interface IEditProps {
  status: Assignment.StatusEnum;
  lecture: Lecture;
  assignment: Assignment;
}


const EditButton = (props: IEditProps) => {
  const [assignmentPulled, setAssignmentPulled] = React.useState(false);
  const fetchAssignmentHandler = async (repo: 'assignment' | 'release') => {
    await pullAssignment(props.lecture.id, props.assignment.id, repo).then(
      () => {
        enqueueSnackbar('Successfully Pulled Repo', {
            variant: 'success'
          }
        );
      },
      error =>
        enqueueSnackbar(error.message, {
          variant: 'error'
        })
    );
  };
  React.useEffect(() => {
    getFiles(`${lectureBasePath}${props.lecture.code}/assignments/${props.assignment.id}`).then(files => {
      console.log(files);
      if (files.length > 0) {
        setAssignmentPulled(true);
      }
    });
  });

  if (!assignmentPulled) {
    return (
      <IconButton
        onClick={(e) => {
          showDialog('Pull Assignment',
            'Do you really want to pull this assignment?',
            async () => {
              await fetchAssignmentHandler('assignment');
            });
          e.stopPropagation();
        }}>
        <FileDownloadIcon sx={{ color: blue[500] }} />
      </IconButton>
    );
  }
  const time = new Date(props.assignment.due_date).getTime();
  if ((props.assignment.due_date !== null && time < Date.now()) || props.status === Assignment.StatusEnum.Complete) {
    return <EditOffIcon sx={{ color: grey[500] }} />;
  } else {
    return (
      <IconButton>
        <EditNoteOutlinedIcon sx={{ color: green[500] }} />
      </IconButton>
    );
  }

};

interface IFeedbackProps {
  feedback_available: boolean;
};

const FeedbackIcon = (props: IFeedbackProps) => {
  if (props.feedback_available) {
    return <DoneIcon sx={{ color: green[500] }} />;
  }
  return <CloseIcon sx={{ color: red[500] }} />;
};

interface IAssignmentTableProps {
  lecture: Lecture;
  rows: AssignmentStudent[];
}


const AssignmentTable = (props: IAssignmentTableProps) => {
  const navigate = useNavigate();
  const headers = [
    { name: 'Name' },
    { name: 'Points', width: 100 },
    { name: 'Deadline', width: 200 },
    { name: 'Edit', width: 75 },
    { name: 'Reset', width: 75 },
    { name: 'Detail View', width: 75 },
    { name: 'Feedback Available', width: 80 }
  ] as IHeaderCell[];

  return (
    <GraderTable<AssignmentStudent>
      headers={headers}
      rows={props.rows}
      rowFunc={row => {
        return (
          <TableRow
            key={row.name}
            component={ButtonTr}
            onClick={() => navigate(`/lecture/${props.lecture.id}/assignment/${row.id}`)}
          >
            <TableCell component='th' scope='row' style={{ width: headerWidth(headers, 'Name') }}>
              <Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>{row.name}</Typography>
              {row.status !== 'released' ?
                <Typography
                  sx={{
                    display: 'inline-block',
                    ml: 0.75,
                    fontSize: 16,
                    color: red[400]
                  }}
                >
                  (not released)
                </Typography> : null}
            </TableCell>
            <TableCell style={{ width: headerWidth(headers, 'Points') }}>{row.points}</TableCell>
            <TableCell style={{ width: headerWidth(headers, 'Deadline') }}>
              <DeadlineComponent component={'chip'} due_date={row.due_date} compact={true} />
            </TableCell>
            <TableCell style={{ width: headerWidth(headers, 'Edit') }}>
              <EditButton status={row.status} lecture={props.lecture} assignment={row} />
            </TableCell>
            <TableCell style={{ width: headerWidth(headers, 'Reset') }}>
              <IconButton
                aria-label='reset'
                size={'small'}
                onClick={(e) => {
                  showDialog(
                    'Reset Assignment',
                    'Do you really want to reset this assignment?',
                    async () => {
                      const assignment = props.rows.find(a => a.id === row.id);
                      try {
                        await pushAssignment(
                          props.lecture.id,
                          assignment.id,
                          'assignment',
                          'Pre-Reset'
                        );
                        await resetAssignment(
                          props.lecture,
                          (assignment as Assignment)
                        );
                        await pullAssignment(
                          props.lecture.id,
                          assignment.id,
                          'assignment'
                        );

                        enqueueSnackbar('Assignment reset successfully', {
                          variant: 'success'
                        });
                      } catch (error: any) {
                        enqueueSnackbar(error.message, {
                          variant: 'error'
                        });
                      }
                    });
                  e.stopPropagation();
                }}
              >
                <RestartAltIcon sx={{ color: blue[500] }} />
              </IconButton>
            </TableCell>
            <TableCell style={{ width: headerWidth(headers, 'Detail View') }}>
              <IconButton aria-label='detail view' size={'small'}>
                <SearchIcon />
              </IconButton>
            </TableCell>
            <TableCell style={{ width: headerWidth(headers, 'Feedback Available') }}>
              <FeedbackIcon feedback_available={row.feedback_available} />
            </TableCell>
          </TableRow>
        );
      }}
    />
  );
};

/*
    * Helper classes & functions for LectureComponent 
    * The goal is to construct an AssignmentStudent class that contains
    * all information that is used by the rows in the assignment table. The
    * sub-routine that accomplishes this is transformAssignments, all other
    * classes and sub-routines below are called from this function.
    * */
interface AssignmentStudent extends AssignmentDetail {
  feedback_available: boolean;

}

/*
    * Scan all submissions return true if feedback is available for that assignment.
    * */
const feedbackAvailable = (submissions: Submission[]): boolean => {
  /* Find the submissions equal to the assignmentId */
  if (submissions === undefined) {
    return false;
  }
  /* If we have a submission, check if it has feedback */
  for (const submission of submissions) {
    if (submission.feedback_available === true) {
      return true;
    }
  }
  return false;
};

/*
    * Transform the AssignmentDetail array into an AssignmentStudent array
    * iterate over the submissions for each assignment, check if there is
    * feedback available for any, then use this to set a flag in the 
    * AssignmentStudent object */
const transformAssignments = (assignments: AssignmentDetail[]): AssignmentStudent[] => {
  const result = [] as AssignmentStudent[];
  for (const assignment of assignments) {
    /* Get any existing submissions */
    const existingSubmissions = assignment.submissions;
    let feedback_available = false;

    /* If there are any submissions, check for feedback! */
    if (existingSubmissions !== undefined) {
      if (existingSubmissions.length > 0) {
        feedback_available = feedbackAvailable(existingSubmissions);
      }
    }
    /* Construct the AssignmentStudent object */
    const assignmentStudent = {
      ...assignment,
      feedback_available: feedback_available
    };
    result.push(assignmentStudent);
  }
  return result;
};

/**
 * Renders the lecture card which contains its assignments.
 */
export const LectureComponent = () => {
  const { lecture, assignments } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: AssignmentDetail[],
  };

  const navigation = useNavigation();

  const newAssignmentSubmissions = transformAssignments(assignments);

  const [lectureState, setLecture] = React.useState(lecture);
  const [assignmentsState, setAssignments] = React.useState(newAssignmentSubmissions);


  if (navigation.state === 'loading') {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }

  /*

   */

  return (
    <Stack direction={'column'} sx={{ m: 5, flex: 1, overflow: 'hidden' }}>
      <Typography variant={'h4'} sx={{ mb: 2 }}>
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
      <Stack><Typography variant={'h6'}>Assignments</Typography></Stack>

      <AssignmentTable lecture={lectureState} rows={assignmentsState} />
    </Stack>
  );
};
