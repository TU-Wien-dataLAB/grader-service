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

import {Assignment} from '../../model/assignment';
import LoadingOverlay from '../util/overlay';
import {Lecture} from '../../model/lecture';
import {getAllSubmissions} from '../../services/submissions.service';
import {getAssignment} from '../../services/assignments.service';
import {AssignmentModalComponent} from './assignment-modal';
import {DeadlineComponent} from '../util/deadline';
import {blue} from '@mui/material/colors';
import {getFiles} from '../../services/file.service';
import {openBrowser} from './overview-view/util';

/**
 * Props for AssignmentComponent.
 */
export interface IAssignmentComponentProps {
  lecture: Lecture;
  assignment: Assignment;
  root: HTMLElement;
  users: any;
  showAlert: (severity: string, msg: string) => void;
  onDeleted: () => void;
}

/**
 * Renders an assignment card which opens onclick the assignment modal.
 * @param props Props of assignment functional component
 * @constructor
 */
export const AssignmentComponent = (props: IAssignmentComponentProps) => {
  const [assignment, setAssignment] = React.useState(props.assignment);
  const [displaySubmissions, setDisplaySubmissions] = React.useState(false);
  const [files, setFiles] = React.useState([]);
  const onSubmissionClose = async () => {
    setDisplaySubmissions(false);
    setAssignment(await getAssignment(props.lecture.id, assignment));
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
          if (submission.auto_status === 'automatically_graded' && !autoUserSet.has(submission.username)) {
            autoUserSet.add(submission.username);
            auto++;
          }
          if (submission.manual_status === 'manually_graded' && !manualUserSet.has(submission.username)) {
            manualUserSet.add(submission.username);
            manual++;
          }
        }
        setNumAutoGraded(auto);
        setNumManualGraded(manual);
      },
      (error: Error) => {
        props.showAlert('error', error.message);
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
    <Box sx={{height: '100%'}}>
      <Card
        sx={{maxWidth: 225, minWidth: 225, height: '100%', m: 1.5}}
        onClick={async () => {
          await openBrowser(
            `source/${props.lecture.code}/${assignment.id}`,
            props.showAlert
          );
          setDisplaySubmissions(true);
        }}
      >
        <CardActionArea
          sx={{height: '100%', display: 'flex', flexDirection: 'column'}}
        >
          <CardContent sx={{flexGrow: 1}}>
            <Typography variant="h5" component="div">
              {assignment.name}
            </Typography>
            <Typography
              sx={{fontSize: 14}}
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
            <Divider sx={{mt: 1, mb: 1}}/>

            <Typography sx={{fontSize: 15, mt: 0.5, ml: 0.5}}>
              {assignment.points}
              <Typography
                color="text.secondary"
                sx={{
                  display: 'inline-block',
                  ml: 0.75,
                  fontSize: 13
                }}
              >
                {'Point' + (assignment.points === 1 ? '' : 's')}
              </Typography>
            </Typography>
            <Typography sx={{fontSize: 15, mt: 0.5, ml: 0.5}}>
              {latestSubmissions.length}
              <Typography
                color="text.secondary"
                sx={{
                  display: 'inline-block',
                  ml: 0.75,
                  fontSize: 13
                }}
              >
                {'Submission' + (latestSubmissions.length === 1 ? '' : 's')}
              </Typography>
            </Typography>
            <Typography sx={{fontSize: 15, mt: 0.5, ml: 0.5}}>
              {numAutoGraded}
              <Typography sx={{fontSize: 10, ml: 0, display: 'inline-block'}}>
                {'/' + latestSubmissions.length}
              </Typography>
              <Typography
                color="text.secondary"
                sx={{
                  display: 'inline-block',
                  ml: 0.75,
                  fontSize: 13
                }}
              >
                {'Autograded Submission' + (numAutoGraded === 1 ? '' : 's')}
              </Typography>
            </Typography>
            <Typography sx={{fontSize: 15, mt: 0.5, ml: 0.5}}>
              {numManualGraded}
              <Typography sx={{fontSize: 10, ml: 0, display: 'inline-block'}}>
                {'/' + latestSubmissions.length}
              </Typography>
              <Typography
                color="text.secondary"
                sx={{
                  display: 'inline-block',
                  ml: 0.75,
                  fontSize: 13
                }}
              >
                {'Manualgraded Submission' + (numManualGraded === 1 ? '' : 's')}
              </Typography>
            </Typography>
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
          showAlert={props.showAlert}
          onClose={onSubmissionClose}
        />
      </LoadingOverlay>
    </Box>
  );
};
