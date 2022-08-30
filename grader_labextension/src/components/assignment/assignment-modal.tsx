// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { Submission } from '../../model/submission';
import { ModalTitle } from '../util/modal-title';
import { Box, Chip, Typography } from '@mui/material';
import { SubmissionList } from './submission-list';
import LoadingOverlay from '../util/overlay';
import { Feedback } from './feedback';
import { AssignmentStatus } from './assignment-status';
import { AssignmentFilesComponent } from './assignment-files';
import { DeadlineComponent } from '../util/deadline';
import WarningIcon from '@mui/icons-material/Warning';

/**
 * Props for AssignmentModalComponent.
 */
export interface IAssignmentModalProps {
  lecture: Lecture;
  assignment: Assignment;
  submissions: Submission[];
  root: HTMLElement;
}

/**
 * Renders the components available in the extended assignment modal view
 * @param props props of assignment modal component
 */
export const AssignmentModalComponent = (props: IAssignmentModalProps) => {
  const [submissions, setSubmissions] = React.useState(props.submissions);
  const [showFeedback, setShowFeedback] = React.useState(false);
  const [feedbackSubmission, setFeedbackSubmission] = React.useState(null);
  /**
   * Opens the feedback view.
   * @param submission submission which feedback will be displayed
   */
  const openFeedback = (submission: Submission) => {
    setFeedbackSubmission(submission);
    setShowFeedback(true);
  };

  React.useEffect(() => {
    setSubmissions(props.submissions);
  }, [props.submissions]);

  return (
    <div style={{ overflow: 'scroll', height: '100%' }}>
      <ModalTitle title={props.assignment.name} />
      <Box sx={{ mt: 10 }}>
        <Typography variant={'h6'} sx={{ ml: 2 }}>
          Status
        </Typography>
        <AssignmentStatus
          lecture={props.lecture}
          assignment={props.assignment}
          submissions={submissions}
        />

        <Typography variant={'h6'} sx={{ ml: 2 }}>
          Files
          <DeadlineComponent
            sx={{ ml: 1 }}
            due_date={props.assignment.due_date}
            compact={false}
            component={'chip'}
          />
        </Typography>
        <AssignmentFilesComponent
          lecture={props.lecture}
          assignment={props.assignment}
          submissions={submissions}
          setSubmissions={setSubmissions}
        />

        <Typography variant={'h6'} sx={{ ml: 2, mt: 3 }}>
          Submissions
          {props.assignment.max_submissions !== null ? (
            <Chip
              sx={{ ml: 2 }}
              size="medium"
              icon={<WarningIcon />}
              label={
                props.assignment.max_submissions -
                submissions.length +
                ' submissions left'
              }
            />
          ) : null}
        </Typography>
        <SubmissionList
          submissions={submissions}
          openFeedback={openFeedback}
          sx={{ m: 2, mt: 1 }}
        />
      </Box>
      <LoadingOverlay
        onClose={() => setShowFeedback(false)}
        open={showFeedback}
        container={props.root}
      >
        <Feedback
          lecture={props.lecture}
          assignment={props.assignment}
          submission={feedbackSubmission}
        />
      </LoadingOverlay>
    </div>
  );
};
