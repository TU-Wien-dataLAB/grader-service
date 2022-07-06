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
import { Button, Stack } from '@mui/material';
import { FilesList } from '../util/file-list';
import PublishRoundedIcon from '@mui/icons-material/PublishRounded';
import GetAppRoundedIcon from '@mui/icons-material/GetAppRounded';
import { AgreeDialog } from '../util/dialog';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import GradingIcon from '@mui/icons-material/Grading';
import { Submission } from '../../model/submission';
import { RepoType } from '../util/repo-type';

/**
 * Props for AssignmentFilesComponent.
 */
export interface IAssignmentFilesComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  showAlert: (severity: string, msg: string) => void;
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
  const path = `${props.lecture.code}/${props.assignment.id}`;
  /**
   * Pulls from given repository by sending a request to the grader git service.
   * @param repo input which repository should be fetched
   */
  const fetchAssignmentHandler = async (repo: 'assignment' | 'release') => {
    try {
      await pullAssignment(props.lecture.id, props.assignment.id, repo);
      props.showAlert('success', 'Successfully Pulled Repo');
    } catch (e) {
      props.showAlert('error', 'Error Fetching Assignment');
    }
  };
  /**
   * Sends request to reset the student changes.
   */
  const resetAssignmentHandler = async () => {
    try {
      await pushAssignment(
        props.lecture.id,
        props.assignment.id,
        'assignment',
        'Pre-Reset'
      );
      await resetAssignment(props.lecture, props.assignment);
      await pullAssignment(props.lecture.id, props.assignment.id, 'assignment');
      props.showAlert('success', 'Successfully Reset Assignment');
    } catch (e) {
      props.showAlert('error', 'Error Reseting Assignment');
    }
    setDialog(false);
  };
  /**
   * Pushes the student submission and submits the assignment
   */
  const submitAssignmentHandler = async () => {
    await submitAssignment(props.lecture, props.assignment, true).then(
      response => {
        props.showAlert('success', 'Successfully Submitted Assignment');
      },
      error => {
        props.showAlert('error', error.message);
      }
    );
    await getAllSubmissions(
      props.lecture,
      props.assignment,
      'none',
      false
    ).then(
      submissions => {
        props.setSubmissions(submissions);
      },
      error => {
        props.showAlert('error', error.message);
      }
    );
  };

  const pushAssignmentHandler = async () => {
    try {
      //TODO add commit message
      await pushAssignment(
        props.lecture.id,
        props.assignment.id,
        RepoType.ASSIGNMENT
      );
      props.showAlert('success', 'Successfully Submitted Assignment');
    } catch (e) {
      props.showAlert('error', 'Error Submitting Assignment');
    }
  };

  return (
    <div>
      <FilesList path={path} showAlert={props.showAlert} sx={{ m: 2, mt: 1 }} />

      <Stack direction={'row'} spacing={1} sx={{ m: 1, ml: 2 }}>
        {props.assignment.type === 'group' && (
          <Button
            variant="outlined"
            size="small"
            onClick={pushAssignmentHandler}
          >
            <PublishRoundedIcon fontSize="small" sx={{ mr: 1 }} />
            Push
          </Button>
        )}

        {props.assignment.type === 'group' && (
          <Button
            variant="outlined"
            size="small"
            onClick={() => fetchAssignmentHandler('assignment')}
          >
            <GetAppRoundedIcon fontSize="small" sx={{ mr: 1 }} />
            Pull
          </Button>
        )}
        <Button
          variant="outlined"
          color="success"
          size="small"
          onClick={() => submitAssignmentHandler()}
        >
          <GradingIcon fontSize="small" sx={{ mr: 1 }} />
          Submit
        </Button>

        <Button
          variant="outlined"
          size="small"
          color="error"
          onClick={() => setDialog(true)}
        >
          <RestartAltIcon fontSize="small" sx={{ mr: 1 }} />
          Reset
        </Button>
      </Stack>

      <AgreeDialog
        open={dialog}
        title={'Reset Assignment'}
        message={
          'This action will delete your current progress and reset the assignment! \n' +
          'Therefore you should copy and paste your work to a different directory before progressing. '
        }
        handleAgree={resetAssignmentHandler}
        handleDisagree={() => setDialog(false)}
      />
    </div>
  );
};
