// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardActions,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography
} from '@mui/material';
import { red } from '@mui/material/colors';

import CheckCircleOutlineOutlinedIcon from '@mui/icons-material/CheckCircleOutlineOutlined';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';

import { Assignment } from '../../model/assignment';
import LoadingOverlay from '../util/overlay';
import { Lecture } from '../../model/lecture';
import { getAllSubmissions } from '../../services/submissions.service';
import {
  getAssignment,
  pullAssignment
} from '../../services/assignments.service';
import { DeadlineComponent } from '../util/deadline';
import { AssignmentModalComponent } from './assignment-modal';
import { Submission } from '../../model/submission';
import { getFiles } from '../../services/file.service';
import { CardDescriptor } from '../util/card-descriptor';
import {
  deleteKey,
  loadNumber,
  storeNumber
} from '../../services/storage.service';
import {openBrowser} from "../coursemanage/overview-view/util";

/**
 * Props for AssignmentComponent.
 */
interface IAssignmentComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  root: HTMLElement;
}

/**
 * Renders an assignment card which displays data abount the assignment status opens onclick the assignment modal.
 * @param props Props of assignment functional component
 */
export const AssignmentComponent = (props: IAssignmentComponentProps) => {
  const [assignment, setAssignment] = React.useState(props.assignment);
  const [displayAssignment, setDisplayAssignment] = React.useState(
    loadNumber('a-opened-assignment') === props.assignment.id || false
  );
  const [submissions, setSubmissions] = React.useState([] as Submission[]);
  const [hasFeedback, setHasFeedback] = React.useState(false);
  const [files, setFiles] = React.useState([]);
  const [bestScore, setBestScore] = React.useState('-');

  React.useEffect(() => {
    getAllSubmissions(props.lecture, assignment, 'none', false).then(
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
    getFiles(`${props.lecture.code}/${assignment.id}`).then(files => {
      if (files.length === 0) {
        pullAssignment(props.lecture.id, assignment.id, 'assignment');
      }
      setFiles(files);
    });

    getAllSubmissions(props.lecture, props.assignment, 'best', false).then(
      submissions => {
        if (submissions.length > 0 && submissions[0].score) {
          setBestScore(submissions[0].score.toString());
        }
      }
    );
  }, [props]);

  /**
   * Executed on assignment modal close.
   */
  const onAssignmentClose = async () => {
    setDisplayAssignment(false);
    deleteKey('a-opened-assignment');
    setAssignment(await getAssignment(props.lecture.id, assignment.id));
    const submissions = await getAllSubmissions(
      props.lecture,
      assignment,
      'none',
      false
    );
    setSubmissions(submissions);
  };

  return (
    <Box sx={{ height: '100%' }}>
      <Card
        sx={{
          maxWidth: 200,
          minWidth: 200,
          height: '100%',
          m: 1.5,
          bgcolor: assignment.status === 'complete' ? '#F1F1F1' : 'white'
        }}
        onClick={async () => {
          await openBrowser(`${props.lecture.code}/${assignment.id}`);
          setDisplayAssignment(true);
          storeNumber('a-opened-assignment', assignment.id);
        }}
      >
        <CardActionArea
          sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        >
          <CardContent sx={{ flexGrow: 1 }}>
            <Typography
              variant="h5"
              component="div"
              color={
                assignment.status === 'complete'
                  ? 'text.disabled'
                  : 'text.primary'
              }
            >
              {assignment.name}
            </Typography>
            <Typography
              sx={{ fontSize: 14 }}
              color="text.secondary"
              gutterBottom
            >
              {files.length + ' File' + (files.length === 1 ? '' : 's')}
              {assignment.status === 'released' ? null : (
                <Typography
                  sx={{
                    fontSize: 12,
                    display: 'inline-block',
                    color: red[500],
                    float: 'right'
                  }}
                >
                  {assignment.status === 'complete'
                    ? 'Completed'
                    : 'Not Released'}
                </Typography>
              )}
            </Typography>
            <Divider sx={{ mt: 1, mb: 1 }} />

            <CardDescriptor
              descriptor={'Submission'}
              value={submissions.length}
            />
            <CardDescriptor
              sx={{ mt: 0.25 }}
              descriptor={(hasFeedback ? 'Has' : 'No') + ' Feedback'}
              value={
                hasFeedback ? (
                  <CheckCircleOutlineOutlinedIcon
                    sx={{ fontSize: 16, mr: -0.25, mb: -0.35 }}
                  />
                ) : (
                  <CancelOutlinedIcon
                    sx={{ fontSize: 16, mr: -0.25, mb: -0.35 }}
                  />
                )
              }
            />
            <CardDescriptor
              descriptor={'Point'}
              value={bestScore}
              ofTotal={assignment.points}
            />
          </CardContent>
          <DeadlineComponent
            due_date={assignment.due_date}
            compact={false}
            component={'card'}
          />
        </CardActionArea>
      </Card>
      <LoadingOverlay
        onClose={onAssignmentClose}
        open={displayAssignment}
        container={props.root}
        transition="zoom"
      >
        <AssignmentModalComponent
          lecture={props.lecture}
          assignment={assignment}
          submissions={submissions}
          root={props.root}
        />
      </LoadingOverlay>
    </Box>
  );
};
