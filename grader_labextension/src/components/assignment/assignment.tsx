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


import { submissionsReducer } from './reducers';
import { AssignmentSubmissions } from './lecture';

import { useParams } from 'react-router-dom';



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

  const { lecture, assignments, assignment_submissions } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    assignment_submissions: AssignmentSubmissions[],
  };


  /* Get the assignment id from router */
  const params = useParams();
  const assignmentId: number = +params["aid"];

  const assignment_submission = assignment_submissions.find(item => item.assignment.id === assignmentId);
  const assignment = assignment_submission.assignment;
  const submissions = assignment_submission.submissions;

  /* Copy assignments out of assignment submissions array */
  const [assignmentState, setAssignment] = React.useState(assignment);


  /* Now we can divvy this into a useReducer  */
  const [submissionsState, dispatchSubmit] = React.useReducer(submissionsReducer, submissions);


  const [displayAssignment, setDisplayAssignment] = React.useState(
      loadNumber('a-opened-assignment') === assignment.id || false
  );

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


  const handleAddSubmission = (submissions: Submission[], submission: Submission) => {
      /* Make the async call here */
      dispatchSubmit({ type: 'add', submission });
  }

  const handleSetAllSubmissions = (submissions: Submission[]) => {
      dispatchSubmit({ type: 'set_all', submission: null });
  };

  React.useEffect(() => {
      getAllSubmissions(lecture.id, assignment.id, 'none', false).then(
          response => {
              handleSetAllSubmissions(response);
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
    handleSetAllSubmissions(submissions);
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
                  submissions={submissions}
                />
            </Box>
            <Box sx={{ mt: 10 }}>
               <Typography variant={'h6'} sx={{ ml: 2 }}>
                 Files
               </Typography>
               <AssignmentFilesComponent 
                 lecture={lecture}
                 assignment={assignment}
                 submissions={submissions}
                 // TODO: figure out what we need to be doing here rather than
                 // passing a dispatch function
                 handleAddSubmission={handleAddSubmission}
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
