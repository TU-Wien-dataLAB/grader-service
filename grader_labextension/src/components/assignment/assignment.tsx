// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Assignment } from '../../model/assignment';
import { AssignmentDetail } from '../../model/assignmentDetail';
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
import { Files } from './files/files';
import WarningIcon from '@mui/icons-material/Warning';
import {
  useRouteLoaderData,
  Outlet,
} from 'react-router-dom';
import {
  getAssignment,
} from '../../services/assignments.service';
import { getFiles, lectureBasePath } from '../../services/file.service';
import { getAllSubmissions } from '../../services/submissions.service';
import {
  deleteKey,
  loadNumber,
} from '../../services/storage.service';
import { useParams } from 'react-router-dom';

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

  const { lecture, assignment, submissions } = useRouteLoaderData('assignment') as {
    lecture: Lecture,
    assignment: Assignment,
    submissions: Submission[],
  };

  /* Get the assignment id from router */
  const params = useParams();
  const assignmentId: number = +params["aid"];

  /* Copy assignments out of assignment submissions array */
  const [assignmentState, setAssignment] = React.useState(assignment);

  /* Now we can divvy this into a useReducer  */
  const [allSubmissions, setAllSubmissions] = React.useState(submissions);


  const [displayAssignment, setDisplayAssignment] = React.useState(
      loadNumber('a-opened-assignment') === assignment.id || false
  );

  const [hasFeedback, setHasFeedback] = React.useState(false)
  const [files, setFiles] = React.useState([]);
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
              setAllSubmissions(response);
              const feedback = response.reduce(
                  (accum: boolean, curr: Submission) => 
                  accum || curr.feedback_available,
                  false
              );
              setHasFeedback(feedback);
          }
      );
      getFiles(`${lectureBasePath}${lecture.code}/assignments/${assignment.id}`).then(files => {
          // TODO: make it really explicit where & who pulls the asssignment
          // files! 
          //if (files.length === 0) {
          //    pullAssignment(lecture.id, assignment.id, 'assignment');
          //}
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
    setAllSubmissions(submissions);
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
               <Files 
                 lecture={lecture}
                 assignment={assignment}
                 submissions={submissions}
                 setSubmissions={setAllSubmissions}
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
