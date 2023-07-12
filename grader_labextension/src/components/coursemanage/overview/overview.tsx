// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';

import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import { ModalTitle } from '../../util/modal-title';
import { OverviewCard } from './overview-card';
import { Box, Grid } from '@mui/material';
import { Files } from './files';
import { GitLog } from './git-log';
import { AssignmentStatus } from './assignment-status';
import { RepoType } from '../../util/repo-type';
import { getGitLog, IGitLogObject } from '../../../services/file.service';
import { Submission } from '../../../model/submission';
import { useRouteLoaderData } from 'react-router-dom';


export const OverviewComponent = () => {
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: { instructors: string[], tutors: string[], students: string[] }
  };
  const { assignment, allSubmissions, latestSubmissions } = useRouteLoaderData('assignment') as {
    assignment: Assignment,
    allSubmissions: Submission[],
    latestSubmissions: Submission[]
  };

  const [assignmentState, setAssignmentState] = React.useState(assignment);
  const [gitLogs, setGitLog] = React.useState([] as IGitLogObject[]);

  const onAssignmentChange = (assignment: Assignment) => {
    setAssignmentState(assignment);
  };

  const updateGitLog = () => {
    getGitLog(lecture, assignment, RepoType.SOURCE, 10).then(logs =>
      setGitLog(logs)
    );
  };

  React.useEffect(() => {
    updateGitLog();
  }, [assignmentState]);

  return (
    <Box>
      <ModalTitle title={assignmentState.name}></ModalTitle>
      <Box sx={{ ml: 3, mr: 3, mb: 3, mt: 3 }}>
        <Grid container spacing={2} alignItems='stretch'>
          <Grid item xs={12} md={12} lg={12}>
            <AssignmentStatus
              lecture={lecture}
              assignment={assignmentState}
              onAssignmentChange={onAssignmentChange}
            />
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <OverviewCard
              lecture={lecture}
              assignment={assignmentState}
              allSubmissions={allSubmissions}
              latestSubmissions={latestSubmissions}
              users={users}
            />
          </Grid>

          <Grid item xs={12} md={6} lg={5}>
            <Files
              lecture={lecture}
              assignment={assignmentState}
              onAssignmentChange={onAssignmentChange}
              updateGitLog={updateGitLog}
            />
          </Grid>

          <Grid item xs={12} md={6} lg={4}>
            <GitLog gitLogs={gitLogs} />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};
