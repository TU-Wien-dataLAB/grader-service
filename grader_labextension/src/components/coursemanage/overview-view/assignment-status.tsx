// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../../../model/assignment';
import {
  Box,
  Button,
  Paper,
  Step,
  StepLabel,
  Stepper,
  Typography
} from '@mui/material';
import * as React from 'react';
import NewReleasesRoundedIcon from '@mui/icons-material/NewReleasesRounded';
import TaskIcon from '@mui/icons-material/Task';
import UndoIcon from '@mui/icons-material/Undo';
import TerminalIcon from '@mui/icons-material/Terminal';

import { AgreeDialog, ReleaseDialog } from '../../util/dialog';
import {
  pushAssignment,
  updateAssignment
} from '../../../services/assignments.service';
import { Lecture } from '../../../model/lecture';

export interface IAssignmentStatusProps {
  lecture: Lecture;
  assignment: Assignment;
  onAssignmentChange: (assignment: Assignment) => void;
  showAlert: (severity: string, msg: string) => void;
}

const getActiveStep = (status: Assignment.StatusEnum) => {
  switch (status) {
    case 'created':
      return 0;
    case 'pushed':
      return 0;
    case 'released':
      return 1;
    case 'complete':
      return 2;
  }
};

export const AssignmentStatus = (props: IAssignmentStatusProps) => {
  const [assignment, setAssignment] = React.useState(props.assignment);
  const [showDialog, setShowDialog] = React.useState(false);
  const [dialogContent, setDialogContent] = React.useState({
    title: '',
    message: '',
    handleAgree: null,
    handleDisagree: null
  });

  const updateAssignmentStatus = async (
    status: 'pushed' | 'released' | 'complete',
    success: string,
    error: string
  ) => {
    try {
      console.log('releasing assignment');
      let a = assignment;
      a.status = status;
      a = await updateAssignment(props.lecture.id, a);
      setAssignment(a);
      props.onAssignmentChange(a);
      props.showAlert('success', success);
    } catch (err) {
      props.showAlert('error', error);
    }
  };

  const handleReleaseAssignment = async () => {
    await updateAssignmentStatus(
      'released',
      'Successfully Released Assignment',
      'Error Releasing Assignment'
    );
  };

  const handlePushAssignment = async (commitMessage: string) => {
    try {
      // Note: has to be in this order (release -> source)
      console.log('pushing assignment');
      await pushAssignment(props.lecture.id, assignment.id, 'release');
      await pushAssignment(
        props.lecture.id,
        assignment.id,
        'source',
        commitMessage
      );
    } catch (err) {
      props.showAlert('error', 'Error Pushing Assignment');
      return;
    }
    await updateAssignmentStatus(
      'pushed',
      'Successfully Pushed Assignment',
      'Error Updating Assignment'
    );
  };

  const closeDialog = () => setShowDialog(false);
  const fontSize = 16;
  const steps = [
    {
      label: 'Edit',
      description: (
        <Box>
          <Typography sx={{ fontSize }}>
            The assignment has been created and files can now be added to be
            pushed. You can commit and pull changes from the remote file repository through the file view or can
            work directly with the underlying git repositories by opening the assignment
            in the terminal (<TerminalIcon color={"primary"} fontSize={"inherit"}/>).
            After you are done working on the files you can release the
            assignment, which makes a final commit with the current state of the
            assignment.
          </Typography>
          <ReleaseDialog
            assignment={assignment}
            handleCommit={handlePushAssignment}
            handleRelease={handleReleaseAssignment}
          >
            <Button sx={{ mt: 1 }} variant="outlined" size="small">
              <NewReleasesRoundedIcon fontSize="small" sx={{ mr: 1 }} />
              Release
            </Button>
          </ReleaseDialog>
        </Box>
      )
    },
    {
      label: 'Released',
      description: (
        <Box>
          <Typography sx={{ fontSize }}>
            The assignment has been released to students and it is not advised
            to push further changes to the repository. If the assignment is over you can mark it as
            complete in the edit menu or right here.
            Undoing the release of the assignment will hide the assignment from students again
            but their local files are unaffected by this action. When re-releasing the
            assignment after significant changes a new commit will be made and you will have to
            instruct users to reset their progress thus far
            or work with separate versions later on.
          </Typography>
          <Button
            sx={{ mt: 1, mr: 1 }}
            onClick={() =>
              updateAssignmentStatus(
                'pushed',
                'Successfully Revoked Assignment',
                'Error Revoking Assignment'
              )
            }
            variant="outlined"
            size="small"
          >
            <UndoIcon fontSize="small" sx={{ mr: 1 }} />
            Undo Release
          </Button>
          <Button
            sx={{ mt: 1 }}
            onClick={() => completeAssignment()}
            variant="outlined"
            size="small"
          >
            <TaskIcon fontSize="small" sx={{ mr: 1 }} />
            Complete
          </Button>
        </Box>
      )
    },
    {
      label: 'Assignment Completed',
      description: (
        <Box>
          <Typography sx={{ fontSize }}>
            The assignment has been completed and is not visible to students
            anymore but all their progress will be saved. When re-activating the assignment it will again show up in the assignment view
            and new submissions can be made given the deadline is set accordingly.
          </Typography>
          <Button
            sx={{ mt: 1 }}
            onClick={() =>
              updateAssignmentStatus(
                'released',
                'Successfully Released Assignment',
                'Error Releasing Assignment'
              )
            }
            variant="outlined"
            size="small"
          >
            <UndoIcon fontSize="small" sx={{ mr: 1 }} />
            Undo Complete
          </Button>
        </Box>
      )
    }
  ];
  const completeAssignment = async () => {
    setDialogContent({
      title: 'Complete Assignment',
      message: `Do you want to mark ${assignment.name} as complete? This action will hide the assignment for all students!`,
      handleAgree: async () => {
        await updateAssignmentStatus(
          'complete',
          'Successfully Updated Assignment',
          'Error Updating Assignment'
        );
        closeDialog();
      },
      handleDisagree: () => closeDialog()
    });
    setShowDialog(true);
  };

  return (
    <Paper elevation={3}>
      <Box sx={{ overflowX: 'auto', p: 3 }}>
        <Stepper
          activeStep={getActiveStep(assignment.status)}
          orientation="horizontal"
        >
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel
                optional={
                  index === 2 ? (
                    <Typography variant="caption">Last step</Typography>
                  ) : null
                }
              >
                {step.label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
        <Typography>
          {steps[getActiveStep(assignment.status)].description}
        </Typography>
      </Box>
      <AgreeDialog open={showDialog} {...dialogContent} />
    </Paper>
  );
};