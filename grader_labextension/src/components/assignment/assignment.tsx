// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { Submission } from '../../model/submission';
import { SectionTitle } from '../util/section-title';
import { Box, Chip, Typography } from '@mui/material';
import { SubmissionList } from './submission-list';
import LoadingOverlay from '../util/overlay';
import { Feedback } from './feedback';
import { AssignmentStatus } from './assignment-status';
import { AssignmentFilesComponent } from './assignment-files';
import { DeadlineComponent } from '../util/deadline';
import WarningIcon from '@mui/icons-material/Warning';
import {
  useRouteLoaderData,
  Outlet,
  Link,
  matchPath,
  useLocation,
  useParams,
  useMatch,
  useMatches
} from 'react-router-dom';


/**
 * Props for AssignmentModalComponent.
 */
export interface IAssignmentModalProps {
  root: HTMLElement;
}

/**
 * Renders the components available in the extended assignment modal view
 * @param props props of assignment modal component
 */
export const AssignmentComponent = (props: IAssignmentModalProps) => {

  const { lecture, assignments } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
  };

  const { assignment, submissions } = useRouteLoaderData('assignment') as {
    assignment: Assignment,
    submissions: Submission[],
  };

  const [submissionsState, setSubmissions] = React.useState(submissions);

  //const params = useParams();
  //const match = useMatch(`/lecture/${params.lid}/assignment/${params.aid}/*`);
  //const tab = match.params['*'];

  //const [showFeedback, setShowFeedback] = React.useState(false);
  //const [feedbackSubmission, setFeedbackSubmission] = React.useState(null);
  ///**
  // * Opens the feedback view.
  // * @param submission submission which feedback will be displayed
  // */
  //const openFeedback = (submission: Submission) => {
  //  setFeedbackSubmission(submission);
  //  setShowFeedback(true);
  //};


  return (
      <Box>
          <Box sx={{
               position: 'absolute',
               bottom: 58,
               top: 35,
               left: 0,
               right: 0,
               overflowY: 'auto'
            }}
            >
             <Box sx={{ mt: 10 }}>
                <Typography variant={'h6'} sx={{ ml: 2 }}>
                  Status
                </Typography>
                <AssignmentStatus
                  assignment={assignment}
                  submissions={submissionsState}
                />
            </Box>
            <Box sx={{ mt: 10 }}>
               <Typography variant={'h6'} sx={{ ml: 2 }}>
                 Files
               </Typography>
               <AssignmentFilesComponent 
                 lecture={lecture}
                 assignment={assignment}
                 submissions={submissionsState}
                 setSubmissions={setSubmissions}
               />
            </Box>
            <Outlet />
          </Box>
        {/*
            <Typography variant={'h6'} sx={{ ml: 2 }}>
              Files
              <DeadlineComponent
                sx={{ ml: 1 }}
                due_date={assignment.due_date}
                compact={false}
                component={'chip'}
              />
            </Typography>
            <AssignmentFilesComponent
              lecture={lecture}
              assignment={assignment}
              submissions={submissions}
              setSubmissions={setSubmissions}
            />

            <Typography variant={'h6'} sx={{ ml: 2, mt: 3 }}>
              Submissions
              {assignment.max_submissions !== null ? (
                <Chip
                  sx={{ ml: 2 }}
                  size="medium"
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
              lecture={lecture}
              assignment={assignment}
              submission={feedbackSubmission}
            />
          </LoadingOverlay>
          */ }
    </Box>
  );
};
