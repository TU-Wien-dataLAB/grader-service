// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { AssignmentDetail } from '../../model/assignmentDetail';
import { Submission } from '../../model/submission';
import {
  Box,
  Button,
  Chip,
  Stack,
  Tooltip,
  Typography
} from '@mui/material';

import { SubmissionList } from './submission-list';
import { AssignmentStatus } from './assignment-status';
import { Files } from './files/files';
import WarningIcon from '@mui/icons-material/Warning';
import {
  useRouteLoaderData,
  Outlet, useNavigate, useLocation
} from 'react-router-dom';
import {
  getAssignment, pullAssignment, pushAssignment, resetAssignment
} from '../../services/assignments.service';
import { getFiles, lectureBasePath } from '../../services/file.service';
import { getAllSubmissions, submitAssignment } from '../../services/submissions.service';
import { enqueueSnackbar } from 'notistack';
import { showDialog } from '../util/dialog-provider';
import { RepoType } from '../util/repo-type';
import PublishRoundedIcon from '@mui/icons-material/PublishRounded';
import GetAppRoundedIcon from '@mui/icons-material/GetAppRounded';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import GradingIcon from '@mui/icons-material/Grading';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { DeadlineDetail } from '../util/deadline';
import moment from 'moment';
import { openBrowser } from '../coursemanage/overview/util';
import OpenInBrowserIcon from '@mui/icons-material/OpenInBrowser';

const calculateActiveStep = (submissions: Submission[]) => {
  const hasFeedback = submissions.reduce(
    (accum: boolean, curr: Submission) => accum || curr.feedback_available,
    false
  );
  if (hasFeedback) {
    return 3;
  }
  if (submissions.length > 0) {
    return 1;
  }
  return 0;
};

/**
 * Renders the components available in the extended assignment modal view
 */
export const AssignmentComponent = () => {
  const navigate = useNavigate();
  const reloadPage = () => navigate(0);

  const { lecture, assignment, submissions } = useRouteLoaderData('assignment') as {
    lecture: Lecture,
    assignment: Assignment,
    submissions: Submission[],
  };

  const path = `${lectureBasePath}${lecture.code}/assignments/${assignment.id}`;

  /* Now we can divvy this into a useReducer  */
  const [allSubmissions, setSubmissions] = React.useState(submissions);

  const [files, setFiles] = React.useState([]);
  const [activeStatus, setActiveStatus] = React.useState(0);

  React.useEffect(() => {
    getAllSubmissions(lecture.id, assignment.id, 'none', false).then(
      response => {
        setSubmissions(response);
      }
    );
    getFiles(path).then(files => {
      // TODO: make it really explicit where & who pulls the asssignment
      // files!
      //if (files.length === 0) {
      //    pullAssignment(lecture.id, assignment.id, 'assignment');
      //}
      setFiles(files);
    });

    let active_step = calculateActiveStep(submissions);
    setActiveStatus(active_step);
  }, []);

  const resetAssignmentHandler = async () => {
    showDialog(
      'Reset Assignment',
      'This action will delete your current progress and reset the assignment!',
      async () => {
        try {
          await pushAssignment(
            lecture.id,
            assignment.id,
            'assignment',
            'Pre-Reset'
          );
          await resetAssignment(lecture, assignment);
          await pullAssignment(
            lecture.id,
            assignment.id,
            'assignment'
          );
          enqueueSnackbar('Successfully Reset Assignment', {
            variant: 'success'
          });
          reloadPage();
        } catch (e) {
          if (e instanceof Error) {
            enqueueSnackbar('Error Reset Assignment: ' + e.message, {
              variant: 'error'
            });
          } else {
            console.error('Error: cannot interpret type unkown as error', e);
          }
        }
      }
    );
  };

  /**
   * Pushes the student submission and submits the assignment
   */
  const submitAssignmentHandler = async () => {
    showDialog(
      'Submit Assignment',
      'This action will submit your current notebooks!',
      async () => {
        await submitAssignment(lecture, assignment, true).then(
          response => {
            console.log('Submitted');
            setSubmissions([response, ...allSubmissions]);
            enqueueSnackbar('Successfully Submitted Assignment', {
              variant: 'success'
            });
          },
          error => {
            enqueueSnackbar(error.message, {
              variant: 'error'
            });
          }
        );
      }
    );
  };

  const pushAssignmentHandler = async () => {
    await pushAssignment(
      lecture.id,
      assignment.id,
      RepoType.ASSIGNMENT
    ).then(
      () =>
        enqueueSnackbar('Successfully Pushed Assignment', {
          variant: 'success'
        }),
      error =>
        enqueueSnackbar(error.message, {
          variant: 'error'
        })
    );
  };
  /**
   * Pulls from given repository by sending a request to the grader git service.
   * @param repo input which repository should be fetched
   */
  const fetchAssignmentHandler = async (repo: 'assignment' | 'release') => {
    await pullAssignment(lecture.id, assignment.id, repo).then(
      () => {
        enqueueSnackbar('Successfully Pulled Repo', {
          variant: 'success'
        });
        getFiles(`${lectureBasePath}${lecture.code}/assignments/${assignment.id}`).then(files => {
          setFiles(files);
        });
      },
      error => {
        enqueueSnackbar(error.message, {
          variant: 'error'
        });
      }
    );
  };

  const isDeadlineOver = () => {
    if (assignment.due_date === null) {
      return false;
    }
    const time = new Date(assignment.due_date).getTime();
    return time < Date.now();
  };

  const isLateSubmissionOver = () => {
    if (assignment.due_date === null) {
      return false;
    }
    let late_submission = assignment.settings.late_submission;
    if (late_submission === null || late_submission.length === 0) {
      late_submission = [{ period: 'P0D', scaling: undefined }]
    }
    const late = moment(assignment.due_date).add(moment.duration(late_submission[late_submission.length - 1].period)).toDate().getTime();
    return late < Date.now();
  };

  const isAssignmentCompleted = () => {
    return assignment.status === 'complete';
  };

  const isMaxSubmissionReached = () => {
    if (assignment.max_submissions === null) {
      return false;
    } else {
      return assignment.max_submissions <= submissions.length;
    }
  };

  const isAssignmentFetched = () => {
    return files.length > 0;
  };


  return (
    <Box sx={{ flex: 1, overflow: 'auto' }}>
      <Box>
        <Box sx={{ mt: 6 }}>
          <Typography variant={'h6'} sx={{ ml: 2 }}>
            Status
          </Typography>
          <AssignmentStatus
            activeStep={activeStatus}
            submissions={submissions}
          />
        </Box>
        <Box sx={{ mt: 2, ml: 2 }}>
          <DeadlineDetail due_date={assignment.due_date} late_submissions={assignment.settings.late_submission || []} />
        </Box>
        <Box sx={{ mt: 4 }}>
          <Typography variant={'h6'} sx={{ ml: 2 }}>
            Files
          </Typography>
          <Files
            lecture={lecture}
            assignment={assignment}

          />
          <Stack direction={'row'} spacing={1} sx={{ m: 1, ml: 2 }}>
            {assignment.type === 'group' && (
              <Tooltip title={'Push Changes'}>
                <Button
                  variant='outlined'
                  size='small'
                  onClick={pushAssignmentHandler}
                >
                  <PublishRoundedIcon fontSize='small' sx={{ mr: 1 }} />
                  Push
                </Button>
              </Tooltip>
            )}

            {assignment.type === 'group' && (
              <Tooltip title={'Pull from Remote'}>
                <Button
                  variant='outlined'
                  size='small'
                  onClick={() => fetchAssignmentHandler('assignment')}
                >
                  <FileDownloadIcon fontSize='small' sx={{ mr: 1 }} />
                  Pull
                </Button>
              </Tooltip>
            )}
            {!isAssignmentFetched() ?
              <Tooltip title={'Fetch Assignment'}>
                <Button
                  variant='outlined'
                  color='primary'
                  size='small'
                  onClick={() => fetchAssignmentHandler('release')}
                >
                  <FileDownloadIcon fontSize='small' sx={{ mr: 1 }} />
                  Fetch
                </Button>
              </Tooltip>
              : null}

            <Tooltip title={'Submit Files in Assignment'}>
              <Button
                variant='outlined'
                color={(!isDeadlineOver()) ? 'success' : 'warning'}
                size='small'
                disabled={
                  isLateSubmissionOver() ||
                  isMaxSubmissionReached() ||
                  isAssignmentCompleted() ||
                  files.length == 0
                }
                onClick={() => submitAssignmentHandler()}
              >
                <GradingIcon fontSize='small' sx={{ mr: 1 }} />
                Submit
              </Button>
            </Tooltip>

            <Tooltip title={'Reset Assignment to Released Version'}>
              <Button
                variant='outlined'
                size='small'
                color='error'
                onClick={() => resetAssignmentHandler()}
              >
                <RestartAltIcon fontSize='small' sx={{ mr: 1 }} />
                Reset
              </Button>
            </Tooltip>
            <Tooltip title={'Show files in JupyterLab file browser'}>
              <Button
                variant='outlined'
                size='small'
                color={'primary'}
                onClick={() => openBrowser(path)}
              >
                <OpenInBrowserIcon fontSize='small' sx={{ mr: 1 }} />
                Show in Filebrowser
              </Button>
            </Tooltip>
          </Stack>
        </Box>
        <Outlet />
      </Box>
      <Box sx={{ mt: 4 }}>
        <Typography variant={'h6'} sx={{ ml: 2, mt: 3 }}>
          Submissions
          {assignment.max_submissions !== null ? (
            <Chip
              sx={{ ml: 2 }}
              size='medium'
              icon={<WarningIcon />}
              label={
                assignment.max_submissions -
                submissions.length +
                ' submissions left'
              }
            />
          ) : null}
        </Typography>
        <SubmissionList
          submissions={allSubmissions}
          sx={{ m: 2, mt: 1 }}
        />
      </Box>
    </Box>
  );
};
