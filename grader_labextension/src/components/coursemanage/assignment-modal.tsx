// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Badge,
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Paper
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FormatListNumberedIcon from '@mui/icons-material/FormatListNumbered';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SettingsIcon from '@mui/icons-material/Settings';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { getAllSubmissions } from '../../services/submissions.service';
import { GradingComponent } from './grading/grading';
import { OverviewComponent } from './overview/overview';
import { Submission } from '../../model/submission';
import { StatsComponent } from './stats/stats';
import { GradeBook } from '../../services/gradebook';
import { loadNumber, storeNumber } from '../../services/storage.service';
import { SettingsComponent } from './settings/settings';
import { useRouteLoaderData } from 'react-router-dom';

export interface IAssignmentModalProps {
  root: HTMLElement;
}

export const AssignmentModalComponent = (props: IAssignmentModalProps) => {
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

  const [latestSubmissionsState, setSubmissions] = React.useState(
    latestSubmissions
  );
  const [navigation, setNavigation] = React.useState(
    loadNumber('cm-navigation', null, assignment) || 0
  );
   // TODO: fix layout of content and navigation! The absolute positioning of the boxes leads to unresponsive breadcrumbs because the box is at top:0
   //  no magic numbers anymore!
  return (
    <Box>
      <Box
        sx={{
          position: 'absolute',
          bottom: 58,
          top: 25,
          left: 0,
          right: 0,
          overflowY: 'auto'
        }}
      >
        {navigation === 0 && (
          <OverviewComponent
            lecture={lecture}
            assignment={assignment}
            allSubmissions={allSubmissions}
            latest_submissions={latestSubmissionsState}
            users={users}
            onClose={() => undefined}
          />
        )}

        {navigation === 1 && (
          <GradingComponent
            lecture={lecture}
            assignment={assignment}
            allSubmissions={allSubmissions}
            root={props.root}
          />
        )}
        {navigation === 2 && (
          <StatsComponent
            lecture={lecture}
            assignment={assignment}
            allSubmissions={allSubmissions}
            latestSubmissions={latestSubmissions}
            users={users}
            root={props.root}
          />
        )}
        {navigation === 3 && (
          <SettingsComponent
            assignment={assignment}
            lecture={lecture}
            submissions={latestSubmissions}
          />
        )}
      </Box>

      <Paper
        sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}
        elevation={3}
      >
        <BottomNavigation
          showLabels
          value={navigation}
          onChange={(event, newValue) => {
            storeNumber('cm-navigation', newValue, null, assignment);
            setNavigation(newValue);
            getAllSubmissions(
              lecture.id,
              assignment.id,
              'latest',
              true
            ).then((response: any) => {
              setSubmissions(response);
            });
          }}
        >
          <BottomNavigationAction label='Overview' icon={<DashboardIcon />} />
          <BottomNavigationAction
            label='Submissions'
            icon={
              <Badge
                color='secondary'
                badgeContent={latestSubmissions?.length}
                showZero={latestSubmissions !== null}
              >
                <FormatListNumberedIcon />
              </Badge>
            }
          />
          <BottomNavigationAction label='Stats' icon={<QueryStatsIcon />} />
          <BottomNavigationAction label='Settings' icon={<SettingsIcon />} />
        </BottomNavigation>
      </Paper>
    </Box>
  );
};
