// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Divider,
  Typography
} from '@mui/material';

import { Assignment } from '../../model/assignment';
import LoadingOverlay from '../util/overlay';
import { Lecture } from '../../model/lecture';
import {
  getAllSubmissions,
  getProperties
} from '../../services/submissions.service';
import {
  getAssignment,
  getAssignmentProperties
} from '../../services/assignments.service';
import { AssignmentModalComponent } from './assignment-modal';
import { DeadlineComponent } from '../util/deadline';
import { blue } from '@mui/material/colors';
import { getFiles } from '../../services/file.service';
import { openBrowser } from './overview-view/util';
import { CardDescriptor } from '../util/card-descriptor';
import { enqueueSnackbar } from 'notistack';
import { GradeBook } from '../../services/gradebook';
import {
  deleteKey,
  loadNumber,
  storeNumber
} from '../../services/storage.service';

/**
 * Props for AssignmentComponent.
 */
export interface IAssignmentComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  root: HTMLElement;
  users: any;
  onDeleted: () => void;
}

/**
 * Renders an assignment card which opens onclick the assignment modal.
 * @param props Props of assignment functional component
 * @constructor
 */
export const AssignmentComponent = (props: IAssignmentComponentProps) => {
  const [assignment, setAssignment] = React.useState(props.assignment);
  const [displaySubmissions, setDisplaySubmissions] = React.useState(
    loadNumber('cm-opened-assignment') === props.assignment.id || false
  );
  const [files, setFiles] = React.useState([]);
  const onSubmissionClose = async () => {
    setDisplaySubmissions(false);
    deleteKey('cm-opened-assignment');
    setAssignment(await getAssignment(props.lecture.id, assignment.id));
    props.onDeleted();
  };

  const [allSubmissions, setAllSubmissions] = React.useState([]);
  const [latestSubmissions, setLatestSubmissions] = React.useState([]);
  const [numAutoGraded, setNumAutoGraded] = React.useState(0);
  const [numManualGraded, setNumManualGraded] = React.useState(0);
  React.useEffect(() => {
    getAllSubmissions(props.lecture, assignment, 'none', true).then(
      response => {
        setAllSubmissions(response);
        let auto = 0;
        const autoUserSet = new Set<string>();
        let manual = 0;
        const manualUserSet = new Set<string>();
        for (const submission of response) {
          if (
            submission.auto_status === 'automatically_graded' &&
            !autoUserSet.has(submission.username)
          ) {
            autoUserSet.add(submission.username);
            auto++;
          }
          if (
            submission.manual_status === 'manually_graded' &&
            !manualUserSet.has(submission.username)
          ) {
            manualUserSet.add(submission.username);
            manual++;
          }
        }
        setNumAutoGraded(auto);
        setNumManualGraded(manual);
      },
      (error: Error) => {
        enqueueSnackbar(error.message, {
          variant: 'error'
        });
      }
    );

    getAllSubmissions(props.lecture, assignment, 'latest', true).then(
      response => {
        setLatestSubmissions(response);
      }
    );

    getFiles(`source/${props.lecture.code}/${assignment.id}`).then(files => {
      setFiles(files);
    });
  }, [assignment]);

  return (
    <Box sx={{ height: '100%' }}>
      <Card
        sx={{ maxWidth: 225, minWidth: 225, height: '100%', m: 1.5 }}
        onClick={async () => {
          await openBrowser(`source/${props.lecture.code}/${assignment.id}`);
          setDisplaySubmissions(true);
          storeNumber('cm-opened-assignment', assignment.id);
        }}
      >
        <CardActionArea
          sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        >
          <CardContent sx={{ flexGrow: 1 }}>
            <Typography variant="h5" component="div">
              {assignment.name}
            </Typography>
            <Typography
              sx={{ fontSize: 14 }}
              color="text.secondary"
              gutterBottom
            >
              {files.length + ' File' + (files.length === 1 ? '' : 's')}
              <Typography
                sx={{
                  fontSize: 12,
                  display: 'inline-block',
                  color: blue[500],
                  float: 'right'
                }}
              >
                {assignment.status}
              </Typography>
            </Typography>
            <Divider sx={{ mt: 1, mb: 1 }} />

            <CardDescriptor
              descriptor={'Point'}
              value={assignment.points}
              fontSizeDescriptor={13}
            />
            <CardDescriptor
              descriptor={'User with Submission'}
              value={latestSubmissions.length}
              fontSizeDescriptor={13}
            />
            <CardDescriptor
              descriptor={'Autograded Submission'}
              value={numAutoGraded}
              ofTotal={latestSubmissions.length}
              fontSizeDescriptor={13}
            />
            <CardDescriptor
              descriptor={'Manualgraded Submission'}
              value={numManualGraded}
              ofTotal={latestSubmissions.length}
              fontSizeDescriptor={13}
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
        onClose={onSubmissionClose}
        open={displaySubmissions}
        container={props.root}
        transition="zoom"
      >
        <AssignmentModalComponent
          lecture={props.lecture}
          assignment={assignment}
          allSubmissions={allSubmissions}
          latestSubmissions={latestSubmissions}
          root={props.root}
          users={props.users}
          onClose={onSubmissionClose}
        />
      </LoadingOverlay>
    </Box>
  );
};
