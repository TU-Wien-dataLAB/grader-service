// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { Submission } from '../../model/submission';
import { 
    Box, 
    Chip,
    Typography
} from '@mui/material';

import { SubmissionList } from './submission-list';
import LoadingOverlay from '../util/overlay';
import { Feedback } from './feedback';
import { AssignmentStatus } from './assignment-status';
import { AssignmentFilesComponent } from './assignment-files';
import WarningIcon from '@mui/icons-material/Warning';
import {
  useRouteLoaderData,
  Outlet,
} from 'react-router-dom';
import {
  getAssignment,
  pullAssignment
} from '../../services/assignments.service';
import { getFiles } from '../../services/file.service';
import { getAllSubmissions } from '../../services/submissions.service';
import {
  deleteKey,
  loadNumber,
} from '../../services/storage.service';


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
  
  const [assignmentState, setAssignment] = React.useState(assignment);
  const [displayAssignment, setDisplayAssignment] = React.useState(
      loadNumber('a-opened-assignment') === assignment.id || false
  );
  const [submissionsState, setSubmissions] = React.useState([] as Submission[]);
  const [hasFeedback, setHasFeedback] = React.useState(false)
  const [files, setFiles] = React.useState([]);
  const [bestScore, setBestScore] = React.useState('-');

  const [activeStatus, setActiveStatus] = React.useState(0);
  
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
      getAllSubmissions(lecture.id, assignment.id, 'none', false).then(
          response => {
              setSubmissions(response);
              const feedback = response.reduce(
                  (accum: boolean, curr: Submission) => 
                  accum || curr.feedback_available,
                  false
              );
              setHasFeedback(feedback);
          }
      );
      getFiles(`${lecture.code}/${assignment.id}`).then(files => {
          if (files.length === 0) {
              pullAssignment(lecture.id, assignment.id, 'assignment');
          }
          setFiles(files);
      });

      getAllSubmissions(lecture.id, assignment.id, 'best', false).then(
          submissions => {
              if (submissions.length > 0 && submissions[0].score) {
                  setBestScore(submissions[0].score.toString());
            }
          }
      );

      let active_step = calculateActiveStep(submissions); 
      setActiveStatus(active_step);

  }, [props]);

  /**
   * Executed on assignment modal close.
   */
  const onAssignmentClose = async () => {
    setDisplayAssignment(false);
    deleteKey('a-opened-assignment');
    setAssignment(await getAssignment(lecture.id, assignment.id));
    const submissions = await getAllSubmissions(
      lecture.id,
      assignment.id,
      'none',
      false
    );
    setSubmissions(submissions);
  };


  return (
      <Box>
      <Box sx={{ height: '100%' }}>
            <Box sx={{ mt: 10 }}>
                <Typography variant={'h6'} sx={{ ml: 2 }}>
                  Status
                </Typography>
                <AssignmentStatus
                  activeStep={activeStatus}
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
          <Box sx={{ mt: 10 }}>
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
    </Box>
  );
};
