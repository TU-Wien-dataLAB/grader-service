// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';

import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { EditDialog } from '../../util/dialog';
import { ModalTitle } from '../../util/modal-title';
import { OverviewCard } from './overview-card';
import { Box, Grid } from '@mui/material';
import { Files } from './files';
import { GitLog } from './git-log';
import {
  getAssignment,
  updateAssignment
} from '../../../services/assignments.service';
import { AssignmentStatus } from './assignment-status';
import { RepoType } from '../../util/repo-type';
import {getGitLog, IGitLogObject} from "../../../services/file.service";
import {Submission} from "../../../model/submission";

export interface IOverviewProps {
  assignment: Assignment;
  lecture: Lecture;
  allSubmissions: Submission[];
  latest_submissions: Submission[];
  users: any;
  onClose: () => void;
}

export const OverviewComponent = (props: IOverviewProps) => {
  const [assignment, setAssignment] = React.useState(props.assignment);
  const [gitLogs, setGitLog] = React.useState([] as IGitLogObject[]);

  const onAssignmentChange = (assignment: Assignment) => {
    setAssignment(assignment);
  };

  const updateGitLog = () => {
    getGitLog(props.lecture, props.assignment, RepoType.SOURCE, 10).then(logs =>
      setGitLog(logs)
    );
  };

  React.useEffect(() => {
    updateGitLog();
  }, [assignment]);

  return (
    <Box>
      <ModalTitle title={assignment.name}>
        <Box sx={{ ml: 2 }} display="inline-block">
          <EditDialog
            lecture={props.lecture}
            assignment={assignment}
            submissions={props.allSubmissions}
            onSubmit={updatedAssignment =>
              updateAssignment(props.lecture.id, updatedAssignment).then(
                response => {
                  setAssignment(response);
                }
              )
            }
            onClose={props.onClose}
          />
        </Box>
      </ModalTitle>
      <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3 }}>
        <Grid container spacing={2} alignItems="stretch">
          <Grid item xs={12} md={12} lg={12}>
            <AssignmentStatus
              lecture={props.lecture}
              assignment={assignment}
              onAssignmentChange={onAssignmentChange}
            />
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <OverviewCard
              lecture={props.lecture}
              assignment={assignment}
              allSubmissions={props.allSubmissions}
              latestSubmissions={props.latest_submissions}
              users={props.users}
            />
          </Grid>

          <Grid item xs={12} md={6} lg={5}>
            <Files
              lecture={props.lecture}
              assignment={assignment}
              onAssignmentChange={onAssignmentChange}
              updateGitLog={updateGitLog}
            />
          </Grid>

          <Grid item xs={12} md={6} lg={4}>
            <GitLog
              gitLogs={gitLogs}
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};
