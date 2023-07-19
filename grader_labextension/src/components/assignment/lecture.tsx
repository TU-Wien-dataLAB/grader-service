// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.
import * as React from 'react';
import moment from 'moment';
import { useNavigate, useNavigation, useRouteLoaderData } from 'react-router-dom';
import {
  Button, IconButton,
  Card,
  LinearProgress, Stack, TableCell, TableRow,
  Typography
} from '@mui/material';
import { red, blue, green } from '@mui/material/colors';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined';
import DoneIcon from '@mui/icons-material/Done';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { enqueueSnackbar } from 'notistack';

import { ButtonTr, GraderTable } from '../util/table';
import { DeadlineComponent, getDisplayDate } from '../util/deadline';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import {
    createAssignment,
    getAllAssignments
} from '../../services/assignments.service';
import { ResetTv } from '@mui/icons-material';

interface IEditProps {
    status: Assignment.StatusEnum;
}

const EditButton = (props: IEditProps) => {
    if (props.status === Assignment.StatusEnum.Released) {
        return <EditNoteOutlinedIcon sx={{ color: green[500] }} />;
    }
    return <FileDownloadIcon sx={{ color: blue[500] }} />;
}

interface ISubmitProps {
    /* This due date is gotten from a deadline component props */
    due_date: string | null;
}

const SubmitButton = (props: ISubmitProps) => {
    if (props.due_date === null) { /* No deadline, woohoo! */
        // TODO: add functionality that makes this fire a submit request 
        return <Button variant='outlined' size={'small'} sx={{ color: green[500] }}>Submit</Button>;
    }
    if (props.due_date !== null) { /* Got help us we have to parse a date string in javascript */
        const date = moment.utc(props.due_date).local().toDate();
        const display_date = getDisplayDate(date, false);
        if (display_date === 'Deadline over!') {
            // TODO: this should never lead anywhere 
            return <Button variant='outlined' size={'small'} sx={{ color: red[500] }}>Deadline over!</Button>;
        }
        // TODO: add functionality that makes this fire a submit request
        return <Button variant='outlined' size={'small'} sx={{ color: green[500] }}>Submit</Button>;
    }
    /* This should never be seen */
    return <Button variant='outlined' size={'small'} sx={{ color: green[500] }}>Grandma's Knickers</Button>; 
};

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
        { name: 'Edit' },
        { name: 'Reset' },
        { name: 'Submit' },
        { name: 'Detail View' },
        { name: 'Feedback Available' }
    ];

    const [showDialog, setShowDialog] = React.useState(false);

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
                        <Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>{row.name}</Typography>
                      </TableCell>
                      <TableCell style={{ width: 34 }}>{row.points}</TableCell>
                      <TableCell>
                        <DeadlineComponent component={'chip'} due_date={row.due_date} compact={true} />
                      </TableCell>
                      <TableCell style={{ width: 55 }}>
                        <IconButton aria-label='Edit' size={'small'}>
                          <EditButton status={row.status} />
                        </IconButton>
                      </TableCell>
                      <TableCell style={{ width: 55 }}>
                        <IconButton aria-label='reset' size={'small'}>
                          <RestartAltIcon sx={{ color: blue[500] }} />
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        <SubmitButton due_date={row.due_date} />
                        </TableCell>
                      <TableCell style={{ width: 55 }}>
                        <IconButton aria-label='detail view' size={'small'}>
                          <SearchIcon />
                        </IconButton>
                      </TableCell>
                      <TableCell style={{width: 55 }}>
                        <IconButton aria-label='feedback available' size={'small'}>
                          <DoneIcon sx={{ color: green[500] }} />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                );
            }}
            />
            </>
    );
};

/**
 * Props for LectureComponent.
 */
interface ILectureComponentProps {
  root: HTMLElement;
}

/**
 * Renders the lecture card which contains it's assignments.
 * @param props Props of the lecture component
 */
export const LectureComponent = (props: ILectureComponentProps) => {
    const { lecture, assignments } = useRouteLoaderData('lecture') as {
        lecture: Lecture,
        assignments: Assignment[], 
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

  /**
   * Toggles collapsable in the card body.
   */
  return (
      <Stack direction={'column'} sx={{ m: 5 }}>
      <Typography variant={'h2'} sx={{ mb: 2 }}>
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
