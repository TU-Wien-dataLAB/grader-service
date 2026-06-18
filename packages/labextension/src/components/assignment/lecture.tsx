/**
 * Copyright (c) 2022, TU Wien
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconButton,
  Card,
  LinearProgress,
  Stack,
  TableCell,
  TableRow,
  Typography,
  Chip
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
import { DeadlineComponent } from '../util/deadline';
import { Assignment } from '../../model/assignment';
import { AssignmentDetail } from '../../model/assignmentDetail';
import { Submission } from '../../model/submission';
import { Lecture } from '../../model/lecture';
import {
  getAllAssignments,
  pullAssignment,
  pushAssignment,
  resetAssignment
} from '../../services/assignments.service';
import { showDialog } from '../util/dialog-provider';
import EditOffIcon from '@mui/icons-material/EditOff';
import CheckIcon from '@mui/icons-material/Check';
import { getFiles, lectureBasePath } from '../../services/file.service';
import { useQuery } from '@tanstack/react-query';
import { getLecture } from '../../services/lectures.service';
import { extractIdsFromBreadcrumbs } from '../util/breadcrumbs';
import { RepoType } from '../util/repo-type';
import { FeedbackStatus } from '../../model/feedbackStatus';
import { GroupsDropDownMenu } from '../util/groups-drop-down-menu';
import { useState } from 'react';

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
  const fetchAssignmentHandler = async (
    repo: RepoType.USER | RepoType.RELEASE
  ) => {
    await pullAssignment(props.lecture.id, props.assignment.id, repo).then(
      () => {
        enqueueSnackbar('Successfully Pulled Repo', {
          variant: 'success'
        });
      },
      error =>
        enqueueSnackbar(error.message, {
          variant: 'error'
        })
    );
  };
  React.useEffect(() => {
    getFiles(
      `${lectureBasePath}${props.lecture.code}/assignments/${props.assignment.id}`
    ).then(files => {
      if (files.length > 0) {
        setAssignmentPulled(true);
      }
    });
  });

  if (!assignmentPulled) {
    return (
      <IconButton
        onClick={e => {
          showDialog(
            'Pull Assignment',
            'Do you really want to pull this assignment?',
            async () => {
              await fetchAssignmentHandler(RepoType.USER);
            }
          );
          e.stopPropagation();
        }}
      >
        <FileDownloadIcon sx={{ color: blue[500] }} />
      </IconButton>
    );
  }
  const time = new Date(props.assignment.settings.deadline).getTime();
  if (
    (props.assignment.settings.deadline !== null && time < Date.now()) ||
    props.status === Assignment.StatusEnum.Complete
  ) {
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
}

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
    { name: 'Group', width: 200 },
    { name: 'Points', width: 100 },
    { name: 'Deadline', width: 200 },
    { name: 'Edit', width: 75 },
    { name: 'Reset', width: 75 },
    { name: 'Detail View', width: 75 },
    { name: 'Feedback Available', width: 80 }
  ] as IHeaderCell[];

  return (
    <>
      {props.rows.length === 0 ? (
        <Typography
          variant="body1"
          align="center"
          color="text.secondary"
          sx={{ mt: 2 }}
        >
          No assignments are currently available.
        </Typography>
      ) : (
        <GraderTable<AssignmentStudent>
          headers={headers}
          rows={props.rows}
          rowFunc={row => {
            return (
              <TableRow
                key={row.name}
                component={ButtonTr}
                onClick={() =>
                  navigate(`/lecture/${props.lecture.id}/assignment/${row.id}`)
                }
              >
                <TableCell
                  component="th"
                  scope="row"
                  style={{ width: headerWidth(headers, 'Name') }}
                >
                  <Typography variant={'subtitle2'} sx={{ fontSize: 16 }}>
                    {row.name}
                  </Typography>
                  {row.status === 'created' || row.status === 'pushed' ? (
                    <Typography
                      sx={{
                        display: 'inline-block',
                        ml: 0.75,
                        fontSize: 16,
                        color: red[400]
                      }}
                    >
                      (not released)
                    </Typography>
                  ) : null}
                  {row.status === 'complete' ? (
                    <Typography
                      sx={{
                        display: 'inline-block',
                        ml: 0.75,
                        fontSize: 16,
                        color: blue[400]
                      }}
                    >
                      (complete)
                    </Typography>
                  ) : null}
                </TableCell>
                <TableCell align={'left'}>
                  {row.settings.group !== '' && row.settings.group !== null && (
                    <Chip
                      label={row.settings.group}
                      color={'primary'}
                      variant={'outlined'}
                    />
                  )}
                </TableCell>
                <TableCell style={{ width: headerWidth(headers, 'Points') }}>
                  {row.points}
                </TableCell>
                <TableCell style={{ width: headerWidth(headers, 'Deadline') }}>
                  <DeadlineComponent
                    component={'chip'}
                    deadline={row.settings.deadline}
                    compact={true}
                  />
                </TableCell>
                <TableCell style={{ width: headerWidth(headers, 'Edit') }}>
                  <EditButton
                    status={row.status}
                    lecture={props.lecture}
                    assignment={row}
                  />
                </TableCell>
                <TableCell style={{ width: headerWidth(headers, 'Reset') }}>
                  <IconButton
                    aria-label="reset"
                    size={'small'}
                    onClick={e => {
                      showDialog(
                        'Reset Assignment',
                        'Do you really want to reset this assignment?',
                        async () => {
                          const assignment = props.rows.find(
                            a => a.id === row.id
                          );
                          try {
                            await pushAssignment(
                              props.lecture.id,
                              assignment.id,
                              RepoType.USER,
                              'Pre-Reset'
                            );
                            await resetAssignment(
                              props.lecture,
                              assignment as Assignment
                            );
                            await pullAssignment(
                              props.lecture.id,
                              assignment.id,
                              RepoType.USER
                            );

                            enqueueSnackbar('Assignment reset successfully', {
                              variant: 'success'
                            });
                          } catch (error: any) {
                            enqueueSnackbar(error.message, {
                              variant: 'error'
                            });
                          }
                        }
                      );
                      e.stopPropagation();
                    }}
                  >
                    <RestartAltIcon sx={{ color: blue[500] }} />
                  </IconButton>
                </TableCell>
                <TableCell
                  style={{ width: headerWidth(headers, 'Detail View') }}
                >
                  <IconButton aria-label="detail view" size={'small'}>
                    <SearchIcon />
                  </IconButton>
                </TableCell>
                <TableCell
                  style={{ width: headerWidth(headers, 'Feedback Available') }}
                >
                  <FeedbackIcon feedback_available={row.feedback_available} />
                </TableCell>
              </TableRow>
            );
          }}
        />
      )}
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
    if (
      submission.feedback_status === FeedbackStatus.Generated ||
      submission.feedback_status === FeedbackStatus.FeedbackOutdated
    ) {
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
const transformAssignments = (
  assignments: AssignmentDetail[]
): AssignmentStudent[] => {
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
  const { lectureId } = extractIdsFromBreadcrumbs();
  const allGroupsValue = 'All';
  const [chosenGroup, setChosenGroup] = useState(allGroupsValue);

  const { data: lecture, isLoading: isLoadingLecture } = useQuery<Lecture>({
    queryKey: ['lecture', lectureId],
    queryFn: () => getLecture(lectureId, true),
    enabled: !!lectureId
  });

  const { data: assignments = [], isLoading: isLoadingAssignments } = useQuery({
    queryKey: ['assignments', lectureId],
    queryFn: () => getAllAssignments(lectureId),
    enabled: !!lecture
  });

  const [assignmentsState, setAssignmentsState] = React.useState([]);

  React.useEffect(() => {
    if (assignments.length > 0) {
      const transformedAssignments = transformAssignments(assignments);
      setAssignmentsState(transformedAssignments);
    }
  }, [assignments]);

  if (isLoadingLecture || isLoadingAssignments) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }

  return (
    <Stack direction={'column'} sx={{ m: 5, flex: 1, overflow: 'hidden' }}>
      <Typography variant={'h4'} sx={{ mb: 2 }}>
        {lecture.name}
        {lecture.complete ? (
          <Chip
            sx={{ ml: 1 }}
            label={'Complete'}
            color="error"
            size="small"
            icon={<CheckIcon />}
          />
        ) : null}
      </Typography>
      <Stack direction={'row'} spacing={2}>
        <Typography variant={'h6'}>Assignments</Typography>
        <GroupsDropDownMenu
          assignments={assignments}
          chosenGroup={chosenGroup}
          setChosenGroup={setChosenGroup}
          allGroupsValue={allGroupsValue}
        />
      </Stack>

      <AssignmentTable
        lecture={lecture}
        rows={
          chosenGroup === allGroupsValue
            ? assignmentsState
            : assignmentsState.filter(a => a.settings.group === chosenGroup)
        }
      />
    </Stack>
  );
};
