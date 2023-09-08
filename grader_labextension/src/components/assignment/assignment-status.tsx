// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Assignment } from '../../model/assignment';
import {
  Card,
  CardContent,
  Step,
  StepLabel,
  Stepper,
  Typography
} from '@mui/material';
import * as React from 'react';
import { getFiles } from '../../services/file.service';

import { Submission } from '../../model/submission';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';

/**
 * Props for AssignmentComponent.
 */
export interface IAssignmentStatusProps {
  //assignment: Assignment;
  submissions: Submission[];
  activeStep: number;
}

/**
 * Renders the assignment status stepper.
 * @param props props of assignment status component
 */
export const AssignmentStatus = (props: IAssignmentStatusProps) => {
  const fontSize = 14;
  const steps = [
    {
      label: 'Pulled',
      description: (
        <Typography sx={{ fontSize }}>
          You pulled from the release repository and can now work on the
          assignment. If you are happy with your solution you can submit it.
          Before the deadline you can always resubmit until you are happy with
          the solution.
        </Typography>
      )
    },
    {
      label: 'Submitted',
      description: (
        <Typography sx={{ fontSize }}>
          You have submitted the assignment {props.submissions.length} time
          {props.submissions.length == 1 ? '' : 's'}. The instructor can review
          each submission, but will most likely prioritise the latest.
        </Typography>
      )
    },
    {
      label: 'Feedback available',
      description: (
        <Typography sx={{ fontSize }}>
          You received feedback for one or more of your submissions! You can
          view the feedback in the list of submission when clicking on the{' '}
          <ChatRoundedIcon sx={{ fontSize }} /> icon. Within the deadline you
          can make more submissions, regardless of whether you already received
          feedback.
        </Typography>
      )
    }
  ];
  //getActiveStep().then(s => setActiveStep(s));

  return (
    <Card elevation={0}>
      <CardContent sx={{ overflowY: 'auto' }}>
        <Stepper activeStep={props.activeStep} orientation='horizontal'>
          {steps.map((step) => (
            <Step key={step.label}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        <Typography sx={{ mt: 2, ml: 2 }}>
          {steps[props.activeStep < 2 ? props.activeStep : 2].description}
        </Typography>
      </CardContent>
    </Card>
  );
};
