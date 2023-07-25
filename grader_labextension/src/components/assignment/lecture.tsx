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

import { AgreeDialog } from '../util/dialog';
import { ButtonTr, GraderTable } from '../util/table';
import { DeadlineComponent, getDisplayDate } from '../util/deadline';
import { Assignment } from '../../model/assignment';
import { Submission } from '../../model/submission';
import { Lecture } from '../../model/lecture';
import { resetAssignment } from '../../services/assignments.service';


/*
    * Buttons for AssignmentTable
    * */
interface IEditProps {
    status: Assignment.StatusEnum;
}

const EditButton = (props: IEditProps) => {
    if (props.status === Assignment.StatusEnum.Released) {
        return <EditNoteOutlinedIcon sx={{ color: green[500] }} />;
    }
    return <FileDownloadIcon sx={{ color: blue[500] }} />;
}

interface IFeedbackProps {
    feedback_available: boolean;
};

const FeedbackButton = (props: IFeedbackProps) => {
    if (props.feedback_available) {
        return <DoneIcon sx={{ color: green[500] }} />;
    }
    return <CloseIcon sx={{ color: red[500] }} />;
}

interface IAssignmentTableProps {
    lecture: Lecture;
    rows: AssignmentStudent[];
}


const AssignmentTable = (props: IAssignmentTableProps) => {
    const navigate = useNavigate(); 
    const headers = [
        { name: 'Name' },
        { name: 'Points', width: 75 },
        { name: 'Deadline' },
        { name: 'Edit' },
        { name: 'Reset' },
        { name: 'Detail View' },
        { name: 'Feedback Available' }
    ];

    /*
        * Deduce the submissions array from the assignment array
        * */

    const [showDialog, setShowDialog] = React.useState(false);
    const [resetFunction, setResetFunction] = React.useState({handleAgree: null as () => void});


    const getResetAssignmentFunction = (assignmentId: number) => {
        return async () => {
            try {
                await resetAssignment(
                    props.lecture,
                    props.rows.find(a => a.id === assignmentId)
                );
                enqueueSnackbar('Assignment reset successfully', { 
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
                        <IconButton 
                           aria-label='reset' 
                           size={'small'}
                           onClick={(e) => {
                               setResetFunction({handleAgree: getResetAssignmentFunction(row.id)});
                               setShowDialog(true);
                               e.stopPropagation();
                           }}
                           >
                          <RestartAltIcon sx={{ color: blue[500] }} />
                        </IconButton>
                      </TableCell>
                      <TableCell style={{ width: 55 }}>
                        <IconButton aria-label='detail view' size={'small'}>
                          <SearchIcon />
                        </IconButton>
                      </TableCell>
                      <TableCell style={{width: 55 }}>
                        <FeedbackButton feedback_available={row.feedback_available} />
                      </TableCell>
                    </TableRow>
                );
            }}
            />
            <AgreeDialog open={showDialog} title={'Reset Assignment'} message={'Do you really want to reset this assignment?'} 
                         handleDisagree={() => setShowDialog(false)} {...resetFunction} />
            </>
    );
};

/*
    * Helper classes & functions for LectureComponent 
    * The goal is to construct an AssignmentStudent class that contains
    * all information that is used by the rows in the assignment table. The
    * sub-routine that accomplishes this is transformAssignments, all other
    * classes and sub-routines below are called from this function.
    * */
/*
    * Extend the Assignment Type with a feedback_available field and submissions
    * array 
    * */
interface AssignmentStudent extends Assignment {
    feedback_available: boolean;
    submissions: Submission[];
}

/*
    * Type to handle the AssignmentSubmissions array
    * */
export interface AssignmentSubmissions {
    assignment: Assignment;
    submissions: Submission[];
};


/*
    * Make an dictionary of the assignment Submissions  
    * hashtable à la Javascript  (i.e. leverages the Object type)
    * */
function make_assignment_submissions_dict(asubmissions: AssignmentSubmissions[]) {
    const result = {} as { [key: number ]: Submission[] };
    for (const asubmission of asubmissions) {
        result[asubmission.assignment.id] = asubmission.submissions;
    }
    return result;
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
}

/*
    * Most important routine for setting up row data for AssignmentTable 
    *
    * Extend the Assignments[] -> AssignmentStudent[] by appending atttributes
    * specific to student view:
    *   - feedback_available boolean 
    *   - submissions array
    * */
const transformAssignments = (assignments: Assignment[], assignment_submissions: AssignmentSubmissions[]): AssignmentStudent[] => {

    const asubs_dict = make_assignment_submissions_dict(assignment_submissions);

    const result = [] as AssignmentStudent[]; 
    for (const assignment of assignments) {
        /* Get any existing submissions */
        const existing_submissions = asubs_dict[assignment.id];

        if ((existing_submissions === undefined) || (existing_submissions.length === 0)) {
            result.push({
                ...assignment,
                feedback_available: false,
                submissions: []
            });
        } else {
            const feedback_available = feedbackAvailable(existing_submissions);
            result.push({
                ...assignment,
                feedback_available: feedback_available,
                submissions: existing_submissions
        });
    }
    return result; 
    }
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
    const { lecture, assignments, assignment_submissions } = useRouteLoaderData('lecture') as {
        lecture: Lecture,
        assignments: Assignment[],
        assignment_submissions: AssignmentSubmissions[],
    };


    const navigation = useNavigation(); 

    const [lectureState, setLecture] = React.useState(lecture); 
    const [assignmentsState, setAssignments] = React.useState(assignments);

    const [assignmentsStudentState, setAssignmentsStudent] = React.useState([] as AssignmentStudent[]);

    React.useEffect(() => {
        const new_assignment_submissions = transformAssignments(assignmentsState, assignment_submissions);
        setAssignmentsStudent(new_assignment_submissions);
    }, []);

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
        <AssignmentTable lecture={lectureState} rows={assignmentsStudentState} />
      </Stack>
      );
};
