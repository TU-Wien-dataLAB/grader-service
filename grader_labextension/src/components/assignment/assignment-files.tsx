// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import {
  pullAssignment,
  pushAssignment,
  resetAssignment
} from '../../services/assignments.service';
import {
  getAllSubmissions,
  submitAssignment
} from '../../services/submissions.service';
import { Button, Stack, Tooltip } from '@mui/material';
import { FilesList } from '../util/file-list';
import PublishRoundedIcon from '@mui/icons-material/PublishRounded';
import GetAppRoundedIcon from '@mui/icons-material/GetAppRounded';
import { AgreeDialog } from '../util/dialog';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import GradingIcon from '@mui/icons-material/Grading';
import { Submission } from '../../model/submission';
import { RepoType } from '../util/repo-type';
import { enqueueSnackbar } from 'notistack';

/**
 * Props for AssignmentFilesComponent.
 */
export interface IAssignmentFilesComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  submissions: Submission[];
  setSubmissions: React.Dispatch<React.SetStateAction<Submission[]>>;
}

/**
 * Renders the file view and additional buttons to submit, push, pull or reset the assignment.
 * @param props Props of the assignment files component
 */
export const AssignmentFilesComponent = (
  props: IAssignmentFilesComponentProps
) => {
  const [dialog, setDialog] = React.useState(false);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });
  const path = `${props.lecture.code}/${props.assignment.id}`;
  /**
   * Pulls from given repository by sending a request to the grader git service.
   * @param repo input which repository should be fetched
   */
  const fetchAssignmentHandler = async (repo: 'assignment' | 'release') => {
    await pullAssignment(props.lecture.id, props.assignment.id, repo).then(
      () =>
        enqueueSnackbar('Successfully Pulled Repo', {
          variant: 'success'
        }),
      error =>
        enqueueSnackbar(error.message, {
          variant: 'error'
        })
    );
  };
  /**
   * Sends request to reset the student changes.
   */
  const resetAssignmentHandler = async () => {
    setDialogContent({
      title: 'Reset Assignment',
      message:
        'This action will delete your current progress and reset the assignment! \n' +
        'Therefore you should copy and paste your work to a different directory before progressing. ',
      handleAgree: async () => {
        try {
          await pushAssignment(
            props.lecture.id,
            props.assignment.id,
            'assignment',
            'Pre-Reset'
          );
          await resetAssignment(props.lecture, props.assignment);
          await pullAssignment(
            props.lecture.id,
            props.assignment.id,
            'assignment'
          );
          enqueueSnackbar('Successfully Reset Assignment', {
            variant: 'success'
          });
        } catch (e) {
          enqueueSnackbar('Error Reset Assignment: ' + e.message, {
            variant: 'error'
          });
        }
        setDialog(false);
      },
      handleDisagree: () => {
        setDialog(false);
      }
    });
    setDialog(true);
  };

  /**
   * Pushes the student submission and submits the assignment
   */
  const submitAssignmentHandler = async () => {
    setDialogContent({
      title: 'Submit Assignment',
      message: 'This action will submit your current notebooks!',
      handleAgree: async () => {
        await submitAssignment(props.lecture, props.assignment, true).then(
          response => {
            props.setSubmissions(oldSubmissions => [
              ...oldSubmissions,
              response
            ]);
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
        setDialog(false);
      },
      handleDisagree: () => setDialog(false)
    });
    setDialog(true);
  };

  const pushAssignmentHandler = async () => {
    await pushAssignment(
      props.lecture.id,
      props.assignment.id,
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

  const isDeadlineOver = () => {
    if (props.assignment.due_date === null) {
      return false;
    }
    const time = new Date(props.assignment.due_date).getTime();
    return time < Date.now();
  };

  const isAssignmentCompleted = () => {
    return props.assignment.status === 'complete';
  };

  const isMaxSubmissionReached = () => {
    if (props.assignment.max_submissions === null) {
      return false;
    } else {
      return props.assignment.max_submissions <= props.submissions.length;
    }
  };

  return (
    <div>
      <FilesList path={path} sx={{ m: 2, mt: 1 }} />

      <Stack direction={'row'} spacing={1} sx={{ m: 1, ml: 2 }}>
        {props.assignment.type === 'group' && (
          <Tooltip title={'Push Changes'}>
            <Button
              variant="outlined"
              size="small"
              onClick={pushAssignmentHandler}
            >
              <PublishRoundedIcon fontSize="small" sx={{ mr: 1 }} />
              Push
            </Button>
          </Tooltip>
        )}

        {props.assignment.type === 'group' && (
          <Tooltip title={'Pull from Remote'}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => fetchAssignmentHandler('assignment')}
            >
              <GetAppRoundedIcon fontSize="small" sx={{ mr: 1 }} />
              Pull
            </Button>
          </Tooltip>
        )}
        <Tooltip title={'Submit Files in Assignment'}>
          <Button
            variant="outlined"
            color="success"
            size="small"
            disabled={
              isDeadlineOver() ||
              isMaxSubmissionReached() ||
              isAssignmentCompleted()
            }
            onClick={() => submitAssignmentHandler()}
          >
            <GradingIcon fontSize="small" sx={{ mr: 1 }} />
            Submit
          </Button>
        </Tooltip>

        <Tooltip title={'Reset Assignment to Released Version'}>
          <Button
            variant="outlined"
            size="small"
            color="error"
            onClick={() => resetAssignmentHandler()}
          >
            <RestartAltIcon fontSize="small" sx={{ mr: 1 }} />
            Reset
          </Button>
        </Tooltip>
      </Stack>

      <AgreeDialog open={dialog} {...dialogContent} />
    </div>
  );
};
